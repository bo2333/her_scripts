#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
判断指定位置是否为软链接，是则删除。

用法:
    ./remove_symlink.py -help
    ./remove_symlink.py <path> [<path> ...]

示例:
    ./remove_symlink.py ~/.hermes/plugins/hermes-lcm
    ./remove_symlink.py /path/a /path/b /path/c

行为:
    - 是软链接（含损坏的软链接） → 删除
    - 存在但不是软链接（普通文件/目录） → 不删除，提示并跳过
    - 路径不存在 → 提示并跳过

返回值:
    0 = 全部处理成功（软链接已删除，或本就不是软链接/不存在）
    1 = 删除失败，或启用 --strict 且存在非软链接路径
"""

import argparse
import os
import sys


class _ArgumentParser(argparse.ArgumentParser):
    """参数错误时返回码为 1，与脚本语义保持一致。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "remove_symlink.py",
        description=(
            "判断指定位置是否为软链接，是则删除；\n"
            "不是软链接（普通文件/目录）或路径不存在时，不删除并跳过。\n"
            "支持一次传入多个路径。"
        ),
        add_help=False,
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("paths", metavar="<path>", nargs="+",
                        help="要检查的路径，可传入多个")
    parser.add_argument("--strict", action="store_true",
                        help="严格模式：若路径存在但不是软链接，视为失败（返回 1）")
    return parser


def handle_path(path: str) -> str:
    """处理单个路径，返回状态字符串之一：

    removed     : 是软链接并已删除
    not_symlink : 存在但不是软链接，未删除
    missing     : 路径不存在
    error       : 删除失败
    """
    # 注意：os.path.islink() 对损坏的软链接仍返回 True
    if os.path.islink(path):
        try:
            os.remove(path)
            return "removed"
        except OSError as exc:
            print(f"[FAIL] 删除软链接失败: {path}: {exc}", file=sys.stderr)
            return "error"

    # 排除软链接后，lexists 判定“存在且不是软链接”
    if os.path.lexists(path):
        return "not_symlink"

    return "missing"


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    failed = False

    for path in args.paths:
        status = handle_path(path)

        if status == "removed":
            print(f"[OK] 已删除软链接: {path}")
        elif status == "not_symlink":
            print(f"[SKIP] 存在但不是软链接，未删除: {path}")
            if args.strict:
                failed = True
        elif status == "missing":
            print(f"[SKIP] 路径不存在: {path}")
        else:  # error
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())