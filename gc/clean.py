#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 Hermes 扩展环境中的垃圾项（只删目标侧，不碰源目录）。

用法:
    ./clean.py -help
    ./clean.py --broken-links
    ./clean.py --orphans
    ./clean.py --broken-links --orphans
    ./clean.py --all --dry-run
    ./clean.py --all --json

安全语义:
    - broken（悬空软链接）: 删除链接本身，不跟随
    - orphan（源不存在的安装）: 删除目标侧；源本就不存在，无副作用
    - invalid（结构异常）: 只报告不删除，建议先跑 doctor.py 人工判断

返回值:
    0 = 无失败（含无可清理项）
    1 = 有删除失败
"""

import argparse
import json
import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, os.pardir, "file"))
sys.path.insert(0, _HERE)
import hermes_paths as hp  # noqa: E402
import scan as scan_mod  # noqa: E402


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser():
    p = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "clean.py",
        description=(
            "清理 Hermes 扩展环境中的垃圾项。\n"
            "只删目标侧，不碰源目录；invalid 仅报告不删除。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("-help", action="help", help="显示帮助并退出")
    p.add_argument("--hermes-home", metavar="<dir>", default=None,
                   help="hermes 根目录（默认 $HOME/.hermes）")
    p.add_argument("--broken-links", action="store_true", help="删除悬空软链接")
    p.add_argument("--orphans", action="store_true", help="删除源不存在的安装")
    p.add_argument("--all", action="store_true",
                   help="等价于 --broken-links --orphans（不含 invalid）")
    p.add_argument("--dry-run", action="store_true", help="只打印计划")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    return p


def _remove(path):
    """删除文件/软链接/目录（软链接只删链接本身）。"""
    if os.path.islink(path) or not os.path.isdir(path):
        os.remove(path)
    else:
        shutil.rmtree(path)


def main(argv=None):
    args = build_parser().parse_args(argv)

    do_broken = args.broken_links or args.all
    do_orphan = args.orphans or args.all
    if not (do_broken or do_orphan):
        print("[ERROR] 至少指定 --broken-links / --orphans / --all 之一",
              file=sys.stderr)
        return 1

    hh = hp.hermes_home(args.hermes_home)
    result = scan_mod.scan(hh)

    plan = []
    if do_broken:
        plan += [("broken", it) for it in result["broken"]]
    if do_orphan:
        plan += [("orphan", it) for it in result["orphan"]]

    removed, failed = [], []

    for cat, it in plan:
        label = f"{it['profile']}/{it['kind']}/{it['name']}"
        if args.dry_run:
            print(f"[dry-run] 将删除 {cat}: {label}  ({it['path']})")
            continue
        try:
            _remove(it["path"])
            removed.append({"category": cat, "path": it["path"],
                            "label": label})
            print(f"[OK]   删除 {cat}: {label}")
        except OSError as exc:
            failed.append({"category": cat, "path": it["path"],
                           "label": label, "error": str(exc)})
            print(f"[FAIL] 删除 {cat}: {label}: {exc}", file=sys.stderr)

    # invalid 仅报告
    if result["invalid"]:
        print(f">> 注意: 发现 {len(result['invalid'])} 个 invalid 项，"
              f"本脚本不自动删除；请运行 doctor.py 人工判断")

    if args.json:
        print(json.dumps({"removed": removed, "failed": failed,
                          "invalid_count": len(result["invalid"])},
                         ensure_ascii=False))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())