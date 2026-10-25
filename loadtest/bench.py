#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""零依赖压测脚本（只用 Python 标准库，Windows 直接跑）。

用法示例：
  python loadtest/bench.py --total 5000 --concurrency 200
  python loadtest/bench.py --total 2000 --concurrency 50 --sku 1001 --out loadtest/d3-db.json

输出：QPS / P50 / P95 / P99 / 成功率 / 业务码分布。
设计说明：用线程池 + urllib，够跑到几千 QPS 的客户端压力；不要用它测上万并发的网络层瓶颈。
"""
import argparse
import json
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor


def one_request(url, timeout):
    start = time.perf_counter()
    code = None
    body = ""
    try:
        req = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.status
            body = resp.read(200).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        code = e.code
        body = e.read(200).decode("utf-8", "ignore")
    except Exception as e:  # 连接被拒 / 超时
        code = -1
        body = str(e)[:120]
    cost_ms = (time.perf_counter() - start) * 1000
    return code, cost_ms, body


def biz_code(body):
    try:
        return json.loads(body).get("code", "?")
    except Exception:
        return "?"


def pct(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    k = min(len(sorted_vals) - 1, max(0, int(round((p / 100.0) * len(sorted_vals) - 0.5))))
    return sorted_vals[k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8080")
    ap.add_argument("--sku", default="1001")
    ap.add_argument("--total", type=int, default=2000, help="总请求数")
    ap.add_argument("--concurrency", type=int, default=100, help="并发线程数")
    ap.add_argument("--user-start", type=int, default=1, help="用户ID起始值（测一人一单时用 1）")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--out", default=None, help="把结果写进 json 文件")
    args = ap.parse_args()

    urls = [
        "{}/api/seckill/{}?userId={}".format(args.base_url, args.sku, args.user_start + i % args.total)
        for i in range(args.total)
    ]
    lock = threading.Lock()
    lat, codes, bizs = [], Counter(), Counter()
    done = [0]
    t0 = time.perf_counter()

    def work(url):
        code, cost, body = one_request(url, args.timeout)
        with lock:
            codes[code] += 1
            bizs[biz_code(body)] += 1
            lat.append(cost)
            done[0] += 1
            if done[0] % 500 == 0:
                print("  已完成 {}/{}  用时 {:.1f}s".format(done[0], args.total, time.perf_counter() - t0))

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        list(pool.map(work, urls))

    wall = time.perf_counter() - t0
    lat.sort()
    ok = codes.get(200, 0)
    result = {
        "total": args.total,
        "concurrency": args.concurrency,
        "wall_sec": round(wall, 2),
        "qps": round(args.total / wall, 1),
        "p50_ms": round(pct(lat, 50), 1),
        "p95_ms": round(pct(lat, 95), 1),
        "p99_ms": round(pct(lat, 99), 1),
        "avg_ms": round(statistics.fmean(lat), 1) if lat else 0,
        "http_ok": ok,
        "http_ok_rate": round(ok / max(1, args.total) * 100, 1),
        "http_codes": dict(codes),
        "biz_codes": dict(bizs),
    }
    print("\n===== 压测结果 =====")
    for k in ("total", "concurrency", "wall_sec", "qps", "avg_ms", "p50_ms", "p95_ms", "p99_ms", "http_ok_rate"):
        print("{:<12} {}".format(k, result[k]))
    print("HTTP 码分布  {}".format(result["http_codes"]))
    print("业务码分布  {}".format(result["biz_codes"]))
    print("\n对账提醒：跑完去数据库/Redis 核对 —— 订单数应 <= 库存数，等于「biz_ok」的数量。")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("已写入 {}".format(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
