#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描 Hermes 扩展环境中的垃圾项。

用法:
    ./scan.py -help
    ./scan.py
    ./scan.py --json
    ./scan.py --category broken
    ./scan.py --hermes-home /opt/hermes

类别:
    broken  = 悬空软链接（islink 且目标不存在）
    orphan  = 目标侧有安装、但源目录 ~/Public/external_* 已不存在
    invalid = 结构异常（bin 下无执行位、目标侧空目录等），需人工判断

返回值:
    0 = 干净
    1 = 发现问题
"""

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, os.pardir, "file"))
import hermes_paths as hp  # noqa: E402


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser():
    p = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "scan.py",
        description="扫描 Hermes 扩展环境中的垃圾项（只读，不修改）。",
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("-help", action="help", help="显示帮助并退出")
    p.add_argument("--hermes-home", metavar="<dir>", default=None,
                   help="hermes 根目录（默认 $HOME/.hermes）")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    p.add_argument("--category", choices=["all", "broken", "orphan", "invalid"],
                   default="all", help="只输出指定类别")
    return p


def scan(hh):
    """返回 dict: {"broken": [...], "orphan": [...], "invalid": [...]}。

    每项为 dict: kind/name/profile/path + 类别特定字段。
    """
    result = {"broken": [], "orphan": [], "invalid": []}

    for kind, name, pname, path, _ in hp.iter_installed(hh):
        base = {"kind": kind, "name": name, "profile": pname, "path": path}

        if os.path.islink(path):
            if not os.path.exists(path):
                item = dict(base, target=os.readlink(path))
                result["broken"].append(item)
            continue  # 非悬空链接不再做 orphan/invalid 检查

        # 非软链接
        if kind == "bin" and os.path.isfile(path):
            try:
                if not (os.stat(path).st_mode & 0o111):
                    result["invalid"].append(
                        dict(base, reason="无可执行位"))
                    continue
            except OSError as exc:
                result["invalid"].append(
                    dict(base, reason=f"stat 失败: {exc}"))
                continue

        if os.path.isdir(path):
            try:
                if not os.listdir(path):
                    result["invalid"].append(
                        dict(base, reason="空目录"))
                    continue
            except OSError:
                pass

        src = hp.source_of(kind, name)
        if not os.path.lexists(src):
            result["orphan"].append(dict(base, source=src))

    return result


def _iter_output(result, category):
    if category in ("all", "broken"):
        for it in result["broken"]:
            yield "broken", it
    if category in ("all", "orphan"):
        for it in result["orphan"]:
            yield "orphan", it
    if category in ("all", "invalid"):
        for it in result["invalid"]:
            yield "invalid", it


def main(argv=None):
    args = build_parser().parse_args(argv)
    hh = hp.hermes_home(args.hermes_home)
    result = scan(hh)

    total = {
        "broken": len(result["broken"]),
        "orphan": len(result["orphan"]),
        "invalid": len(result["invalid"]),
    }

    if args.json:
        payload = {"summary": total, "items": result}
        if args.category != "all":
            payload = {"summary": {args.category: total[args.category]},
                       "items": {args.category: result[args.category]}}
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for cat, it in _iter_output(result, args.category):
            label = f"{it['profile']}/{it['kind']}/{it['name']}"
            if cat == "broken":
                print(f"[broken]  {label}  -> {it['target']}")
            elif cat == "orphan":
                print(f"[orphan]  {label}  源不存在: {it['source']}")
            else:
                print(f"[invalid] {label}  {it['reason']}")
        print(f"汇总: broken={total['broken']} orphan={total['orphan']} "
              f"invalid={total['invalid']}")

    return 1 if any(total.values()) else 0


if __name__ == "__main__":
    sys.exit(main())