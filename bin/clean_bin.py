#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卸载 hermes-agent 可执行文件。

用法:
    ./clean_bin.py -help
    ./clean_bin.py <bin> [profile]

说明:
    bin 没有 hermes 注册命令，直接删除文件/目录（软链接只删链接本身）。
    源目录 external_bin 不受影响。

返回值:
    0 = 成功（含目标本就不存在）
    1 = 删除失败
"""

import argparse
import os
import shutil
import sys


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser():
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "clean_bin.py",
        description=(
            "卸载 hermes-agent 可执行文件。\n"
            "default: $HOME/.hermes/bin/<bin>\n"
            "profile: $HOME/.hermes/profiles/<name>/bin/<bin>\n"
            "直接删除文件/目录（软链接只删链接本身），不触碰源目录。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("bin", metavar="<bin>", help="可执行文件/目录名")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="Profile 名称；省略或传 default 表示主 default profile")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根目录（默认 $HOME/.hermes）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划")
    return parser


def purge(path):
    if os.path.islink(path) or not os.path.isdir(path):
        os.remove(path)
    else:
        shutil.rmtree(path)


def main(argv=None):
    args = build_parser().parse_args(argv)
    raw_profile = args.profile
    is_default = raw_profile is None or raw_profile == "default"

    home = os.path.expanduser("~")
    hermes_home = (os.path.abspath(os.path.expanduser(args.hermes_home))
                   if args.hermes_home
                   else os.path.join(home, ".hermes"))

    if is_default:
        target = os.path.join(hermes_home, "bin", args.bin)
        mode = "default"
    else:
        target = os.path.join(hermes_home, "profiles", raw_profile, "bin", args.bin)
        mode = f"profile [{raw_profile}]"

    print(f">> 模式: {mode}")
    print(f">> 目标: {target}")

    if not os.path.lexists(target):
        print(f">> 目标不存在，无需删除: {target}")
        return 0

    if args.dry_run:
        print(">> [dry-run] 将删除目标（软链接只删链接本身）")
        return 0

    try:
        purge(target)
    except OSError as exc:
        print(f"[FAIL] 删除失败: {exc}", file=sys.stderr)
        return 1

    print(f"✅ 已删除: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())