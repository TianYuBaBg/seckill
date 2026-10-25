#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""每天第一件事：跑这个，告诉你今天干什么、怎么验收。

用法：
    python tools/today.py            # 看今天该干什么
    python tools/today.py --verify   # 看完直接跑当天的自检

它读两个文件：
    PLAN.md     —— 14 天的任务清单（找当天那一节）
    PROGRESS.md —— 你打过的卡（决定你的进度）
"""
import argparse
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(ROOT, "PLAN.md")
PROGRESS = os.path.join(ROOT, "PROGRESS.md")
VERIFY = os.path.join(ROOT, "tools", "verify.py")

# 每个 Day 对应 verify.py 的哪一档（没验收命令的用 None）
VERIFY_DAY = {1: 1, 2: 3, 3: 4}


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def plan_sections():
    """返回 {day: [标题, 正文...]}"""
    text = read(PLAN)
    out = {}
    for m in re.finditer(r"^##\s*D(\d+)\s*·\s*(.+?)$", text, re.M):
        day = int(m.group(1))
        start = m.end()
        nxt = re.search(r"^##\s", text[start:], re.M)
        body = text[start:start + nxt.start()] if nxt else text[start:]
        out[day] = (m.group(2).strip(), body.strip())
    return out


def done_days():
    """从 PROGRESS.md 里数出已经打勾完成的最大 Day"""
    if not os.path.exists(PROGRESS):
        return 0
    days = []
    for line in read(PROGRESS).splitlines():
        m = re.match(r"\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*D(\d+)\s*\|", line)
        if m and "__" not in line:
            days.append(int(m.group(2)))
    return max(days) if days else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="看完直接跑当天自检")
    ap.add_argument("--day", type=int, help="指定看哪一天")
    args = ap.parse_args()

    if not os.path.exists(PLAN):
        print("找不到 PLAN.md，确认你在项目根目录")
        return 1

    sections = plan_sections()
    done = done_days()
    today = args.day or min(done + 1, max(sections) if sections else 14)

    if today not in sections:
        print("PLAN.md 里没有 D%d" % today)
        return 1

    title, body = sections[today]
    bar = "=" * 60
    print(bar)
    print("  今天：D%d · %s" % (today, title))
    print("  你已完成：%d/14 天" % done)
    print(bar)
    print(body)
    print(bar)

    vd = VERIFY_DAY.get(today)
    if vd:
        print("  验收命令： python tools/verify.py --day %d" % vd)
        if args.verify:
            print()
            return subprocess.call([sys.executable, VERIFY, "--day", str(vd)])
    else:
        print("  今天没有自动验收，做完跟我说一声，我人工看代码和日志。")

    print("\n  提醒：中间件在 WSL 里，先跑 tools\\start.ps1 再起应用。")
    print("  做完记得：追加 PROGRESS.md 一行 + git commit + git push。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
