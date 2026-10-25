#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自检 —— 跑完当天的任务后先自己过一遍，绿了再叫我验收。

用法（在 D:\\me\\seckill 目录下，且 docker compose 已启动）：

    python tools/verify.py --day 1
    python tools/verify.py --day 2
    python tools/verify.py --day 3

只依赖 Python 标准库。退出码 0 = 全绿。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

import urllib.request

APP = "http://localhost:8080"
REDIS_CONTAINER = "seckill-redis"
MYSQL_CONTAINER = "seckill-mysql"

ok_count = 0
fail_count = 0


def check(name, fn):
    global ok_count, fail_count
    try:
        detail = fn()
        ok_count += 1
        print(f"  [PASS] {name}" + (f" —— {detail}" if detail else ""))
        return True
    except Exception as exc:  # noqa: BLE001
        fail_count += 1
        print(f"  [FAIL] {name} —— {exc}")
        return False


def run(cmd, **kw):
    p = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, **kw)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def http_json(url, method="GET", timeout=10):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def docker_available():
    if not shutil.which("docker"):
        raise RuntimeError("找不到 docker 命令：Docker Desktop 没装好或没启动")
    code, out = run(["docker", "info", "--format", "{{.ServerVersion}}"])
    if code != 0:
        raise RuntimeError("docker 引擎没起来（Docker Desktop 是否在运行？）")
    return out.strip()


def compose_healthy():
    code, out = run(["docker", "compose", "ps", "--format", "json"])
    if code != 0:
        raise RuntimeError("docker compose ps 失败，确认在 D:\\me\\seckill 目录下执行")
    services = []
    for line in out.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            services.append(json.loads(line))
        except json.JSONDecodeError:
            # 老版本 docker compose 输出是表格，退化为文本判断
            services.append({"Name": line, "State": line})
    if len(services) < 3:
        raise RuntimeError(f"只看到 {len(services)} 个服务，应该是 3 个（mysql/redis/rabbitmq）")
    unhealthy = [s for s in services if "healthy" not in str(s.get("Status", s.get("State", ""))).lower()
                 and "running" not in str(s.get("State", "")).lower()]
    if unhealthy:
        raise RuntimeError(f"有服务没起来：{[s.get('Name') for s in unhealthy]}")
    return f"{len(services)} 个服务在跑"


def app_health():
    data = http_json(f"{APP}/actuator/health")
    if data.get("status") != "UP":
        raise RuntimeError(f"应用状态是 {data.get('status')}，不是 UP")
    return data.get("status")


def redis_ping():
    code, out = run(["docker", "exec", REDIS_CONTAINER, "redis-cli", "ping"])
    if code != 0 or "PONG" not in out:
        raise RuntimeError(f"redis-cli ping 返回异常：{out.strip()[:80]}")
    return "PONG"


DB_PASSWORD = os.environ.get("SECKILL_DB_PASSWORD", "root")


def mysql_query(sql):
    code, out = run([
        "docker", "exec", MYSQL_CONTAINER, "mysql", "-uroot", f"-p{DB_PASSWORD}", "-N", "-B",
        "seckill", "-e", sql,
    ])
    if code != 0:
        raise RuntimeError(f"mysql 查询失败：{out.strip()[:120]}")
    return out.strip()


def stock_is_1000():
    val = mysql_query("SELECT stock FROM t_seckill_stock WHERE id = 1;")
    if val != "1000":
        raise RuntimeError(f"库存是 {val}，应该是 1000（跑过压测就 TRUNCATE 后重灌 init.sql）")
    return "stock=1000"


def tables_exist():
    val = mysql_query("SHOW TABLES;").splitlines()
    need = {"t_seckill_stock", "t_seckill_order"}
    missing = need - set(v.strip() for v in val)
    if missing:
        raise RuntimeError(f"缺表：{missing}（init.sql 没执行成功）")
    return ", ".join(sorted(need))


def seckill_endpoint_exists():
    code, out = run(["curl", "-s", "-o", "NUL", "-w", "%{http_code}", "-X", "POST",
                     f"{APP}/api/seckill/1?userId=1"])
    http = out.strip() if code == 0 else ""
    if http != "200":
        raise RuntimeError(f"POST /api/seckill/1 返回 HTTP {http or '连不上'}，应该是 200（接口存在且应用在跑）")
    return "HTTP 200"


def bench_report_exists():
    import glob
    files = sorted(glob.glob("loadtest/report_*.md"))
    if not files:
        raise RuntimeError("没找到 loadtest/report_*.md，压测脚本还没跑过")
    text = open(files[-1], encoding="utf-8").read()
    if "QPS" not in text:
        raise RuntimeError(f"{files[-1]} 里没有 QPS 数据")
    return files[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int, default=1, choices=[1, 2, 3])
    args = ap.parse_args()
    d = args.day

    print(f"== Day {d} 自检 ==")
    check("Docker 引擎可用", docker_available)
    check("三个容器都在跑", compose_healthy)
    check("Redis 可 ping", redis_ping)
    check("MySQL 可连", lambda: mysql_query("SELECT 1;") or "ok")
    check("应用 /actuator/health = UP", app_health)

    if d >= 2:
        check("建表完成", tables_exist)
        check("初始库存 1000", stock_is_1000)

    if d >= 3:
        check("秒杀接口可访问", seckill_endpoint_exists)
        check("已有压测报告", bench_report_exists)

    print(f"\n结果：{ok_count} 通过 / {fail_count} 失败")
    if fail_count:
        print("把 FAIL 那一行发我，我给你定位。")
        return 1
    print("全绿，可以叫验收了：跟我说「Day %d 完成」" % d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
