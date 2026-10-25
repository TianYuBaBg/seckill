#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自检 —— 跑完当天的任务后先自己过一遍，绿了再叫我验收。

你的环境是「Windows 上跑 Java 应用 + WSL(Ubuntu 22.04) 里跑 MySQL/Redis/RabbitMQ」，
没有装 Docker，所以脚本会自动判断走哪条路：

    模式 A（你现在用的，WSL 直装）：mysql / redis 通过 `wsl` 进 Ubuntu 执行命令
    模式 B（以后装了 Docker Desktop）：走 docker exec

用法（在项目根目录，应用已启动）：

    python tools/verify.py --day 1
    python tools/verify.py --day 2
    python tools/verify.py --day 3

只依赖 Python 标准库。退出码 0 = 全绿。
"""
import argparse
import glob
import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request

APP = "http://127.0.0.1:8080"
MYSQL_CONTAINER = "seckill-mysql"
REDIS_CONTAINER = "seckill-redis"
WSL_DISTRO = "Ubuntu-22.04"
DB_PASSWORD = os.environ.get("SECKILL_DB_PASSWORD", "root")
PORTS = {3306: "MySQL", 6379: "Redis", 5672: "RabbitMQ"}

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
    p = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", **kw)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def http_json(url, method="GET", timeout=10):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wsl(cmd):
    """在 WSL Ubuntu 里执行一条 bash 命令。"""
    if not shutil.which("wsl"):
        raise RuntimeError("找不到 wsl 命令")
    return run(["wsl", "-d", WSL_DISTRO, "-u", "root", "--", "bash", "-c", cmd])


def docker_ready():
    if not shutil.which("docker"):
        return False
    code, _ = run(["docker", "info", "--format", "{{.ServerVersion}}"])
    return code == 0


def tcp_open(host, port, timeout=5.0):
    with socket.create_connection((host, port), timeout=timeout):
        return True


def _retry_tcp(host, port, tries=3, gap=1.0):
    import time as _t
    for i in range(tries):
        try:
            return tcp_open(host, port)
        except Exception:
            if i == tries - 1:
                raise
            _t.sleep(gap)


def middleware_ports():
    dead = [f"{name}({port})" for port, name in PORTS.items()
            if not _try(_retry_tcp, "127.0.0.1", port)]
    if dead:
        raise RuntimeError(f"连不上：{', '.join(dead)}（WSL 里没起？试试 wsl -d {WSL_DISTRO} -u root -- systemctl start mysql redis-server rabbitmq-server）")
    return "3306 / 6379 / 5672 都可连"


def _try(fn, *a):
    try:
        return fn(*a)
    except OSError:
        return False


def app_health():
    """整体 UP，且 db / redis / rabbit 三个组件都 UP。"""
    try:
        data = http_json(f"{APP}/actuator/health")
    except urllib.error.HTTPError as exc:  # 503 = 有组件 DOWN
        data = json.loads(exc.read().decode("utf-8"))
        bad = [f"{k}={v.get('status')}" for k, v in (data.get("components") or {}).items()
               if v.get("status") != "UP"]
        raise RuntimeError(f"应用在跑但组件不健康：{', '.join(bad)}") from exc
    if data.get("status") != "UP":
        raise RuntimeError(f"应用状态是 {data.get('status')}")
    comps = {k: v.get("status") for k, v in (data.get("components") or {}).items()}
    return "UP（" + ", ".join(f"{k}:{v}" for k, v in comps.items()) + "）"


def mysql_query(sql):
    """优先 docker exec，其次 wsl 直连。"""
    if docker_ready():
        code, out = run(["docker", "exec", MYSQL_CONTAINER, "mysql", "-uroot",
                         f"-p{DB_PASSWORD}", "-N", "-B", "seckill", "-e", sql])
        if code == 0:
            return out.strip()
    code, out = wsl(f"mysql -uroot -p{DB_PASSWORD} -N -B seckill -e \"{sql}\" 2>/dev/null")
    if code != 0 or not out.strip():
        raise RuntimeError(f"mysql 查询失败：{out.strip()[:120] or '无输出'}")
    return out.strip()


def redis_ping():
    if docker_ready():
        code, out = run(["docker", "exec", REDIS_CONTAINER, "redis-cli", "ping"])
        if code == 0 and "PONG" in out:
            return "PONG"
    code, out = wsl("redis-cli ping 2>/dev/null")
    if code != 0 or "PONG" not in out:
        raise RuntimeError(f"redis-cli ping 返回异常：{out.strip()[:80] or '无输出'}")
    return "PONG"


def stock_is_1000():
    val = mysql_query("SELECT stock FROM sku_stock WHERE sku_id = 1001;")
    if val != "1000":
        raise RuntimeError(f"库存是 {val}，应该是 1000（跑过压测后重灌 sql/init.sql）")
    return "stock=1000"


def tables_exist():
    rows = mysql_query("SHOW TABLES;").splitlines()
    need = {"sku_stock", "seckill_order"}
    missing = need - set(r.strip() for r in rows)
    if missing:
        raise RuntimeError(f"缺表：{missing}（sql/init.sql 没执行成功）")
    return ", ".join(sorted(need))


def seckill_endpoint_ok():
    """POST 秒杀接口，只要不是 404/连接失败就算接口存在（D2 之前返回 501 属正常）。"""
    req = urllib.request.Request(f"{APP}/api/seckill/1001?userId=1", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", "replace")
            return f"HTTP {resp.status} {body[:60]}"
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"接口返回 HTTP {exc.code}（应用没跑起来？）") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"连不上 {APP}：{exc.reason}") from exc


def bench_report_exists():
    files = sorted(glob.glob("loadtest/report_*.md"))
    if not files:
        raise RuntimeError("没找到 loadtest/report_*.md，压测脚本还没跑过")
    text = open(files[-1], encoding="utf-8").read()
    if "QPS" not in text:
        raise RuntimeError(f"{files[-1]} 里没有 QPS 数据")
    return files[-1]



# ---------------- D2：DB 扣减版秒杀闭环 ----------------

def _reset_stock():
    """把库存和订单清回初始态（压测/重复自检前用）。"""
    sql = ("TRUNCATE TABLE seckill_order;"
           "UPDATE sku_stock SET stock = 1000, sold = 0, version = 0 WHERE sku_id = 1001;")
    mysql_query(sql)


def _post_seckill(user_id=1):
    req = urllib.request.Request(f"{APP}/api/seckill/1001?userId={user_id}", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def d2_flow():
    """D2 验收：重置 -> 扣 1 件 -> 库存 999 + 订单 1 条。"""
    _reset_stock()
    if mysql_query("SELECT stock FROM sku_stock WHERE sku_id = 1001;") != "1000":
        raise RuntimeError("重置库存失败")
    status, body = _post_seckill(1)
    if status != 200:
        raise RuntimeError(f"接口返回 HTTP {status}：{body[:80]}")
    if body.strip().startswith("{"):
        import json as _json
        data = _json.loads(body)
        code = str(data.get("code"))
        if code not in ("0", "200"):
            raise RuntimeError(f"业务码是 {code}，不是成功：{body[:80]}")
    stock = mysql_query("SELECT stock FROM sku_stock WHERE sku_id = 1001;")
    if stock != "999":
        raise RuntimeError(f"库存是 {stock}，期望 999（扣减没生效/没走事务）")
    orders = mysql_query("SELECT COUNT(*) FROM seckill_order WHERE sku_id = 1001;")
    if orders != "1":
        raise RuntimeError(f"订单数是 {orders}，期望 1（订单没落库）")
    return "200 成功 / stock=999 / 订单 1 条"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int, default=1, choices=[1, 2, 3, 4])
    args = ap.parse_args()
    d = args.day

    mode = "Docker" if docker_ready() else "WSL 直装"
    print(f"== Day {d} 自检（模式：{mode}）==")
    check("中间件端口可连（3306/6379/5672）", middleware_ports)
    check("Redis 可 ping", redis_ping)
    check("MySQL 可连", lambda: "ok" if mysql_query("SELECT 1;") == "1" else "有响应")
    check("应用 /actuator/health 全 UP", app_health)

    if d >= 2:
        check("建表完成", tables_exist)
        check("初始库存 1000", stock_is_1000)

    if d >= 3:
        check("D2 秒杀闭环（扣库存 + 落订单）", d2_flow)

    if d >= 4:
        check("已有压测报告", bench_report_exists)

    print(f"\n结果：{ok_count} 通过 / {fail_count} 失败")
    if fail_count:
        print("把 FAIL 那一行发我，我给你定位。")
        return 1
    print(f"全绿，可以叫验收了：跟我说「Day {d} 完成」")
    return 0


if __name__ == "__main__":
    sys.exit(main())
