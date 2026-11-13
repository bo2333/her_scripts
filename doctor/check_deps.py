#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查脚本运行依赖（Python / hermes CLI / rsync / git）。

用法:
    ./check_deps.py -help
    ./check_deps.py
    ./check_deps.py --json
    ./check_deps.py --require-all

返回值:
    0 = 必要依赖齐全（--require-all 时全部齐全）
    1 = 缺必要依赖（python 版本不足 / hermes 不存在）
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys


MIN_PY = (3, 10)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser():
    p = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "check_deps.py",
        description="检查脚本运行依赖：Python 版本、hermes CLI、rsync、git。",
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("-help", action="help", help="显示帮助并退出")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    p.add_argument("--require-all", action="store_true",
                   help="rsync/git 也视为必需（默认仅 WARN）")
    return p


def _version_of(cmd):
    """尝试执行 `<cmd> --version` 取第一行；失败返回 None。"""
    try:
        r = subprocess.run([cmd, "--version"], capture_output=True, text=True)
        out = (r.stdout or r.stderr or "").strip().splitlines()
        return out[0] if out else ""
    except (OSError, IndexError):
        return None


def check_python():
    cur = sys.version_info[:2]
    ok = cur >= MIN_PY
    return {
        "name": "python",
        "ok": ok,
        "level": "PASS" if ok else "FAIL",
        "required": True,
        "detail": f"{cur[0]}.{cur[1]} (需要 >= {MIN_PY[0]}.{MIN_PY[1]})",
    }


def check_bin(name, required):
    path = shutil.which(name)
    ok = path is not None
    ver = _version_of(name) if ok else None
    level = "PASS" if ok else ("FAIL" if required else "WARN")
    detail = ver if ok and ver else (path or "未找到")
    return {
        "name": name,
        "ok": ok,
        "level": level,
        "required": required,
        "detail": detail,
    }


def main(argv=None):
    args = build_parser().parse_args(argv)

    deps = [
        check_python(),
        check_bin("hermes", required=True),
        check_bin("rsync", required=args.require_all),
        check_bin("git", required=args.require_all),
    ]

    failed = any(d["level"] == "FAIL" for d in deps)

    if args.json:
        print(json.dumps({"deps": deps, "ok": not failed}, ensure_ascii=False))
    else:
        for d in deps:
            print(f"[{d['level']}] {d['name']:<10} {d['detail']}")
        print(f"汇总: {'OK' if not failed else 'FAIL'}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())