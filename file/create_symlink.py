#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建或更新软链接

说明:
    源可以是文件或目录；源会被 realpath 解析（链中链会被展平）。
    源是悬空软链接（指向不存在目标）时视为"源不存在"而失败。

用法:
    ./create_symlink.py -help
    ./create_symlink.py <源目录> <目标目录>

返回值:
    0 = 成功
    1 = 失败

示例:
    cd ~/.hermes/scripts && chmod +x create_symlink.py
    ./create_symlink.py /path/to/source /path/to/target
    python3 create_symlink.py /path/to/source /path/to/target
"""

import argparse
import os
import shutil
import sys


class _ArgumentParser(argparse.ArgumentParser):
    """参数错误时返回码为 1，与脚本语义保持一致。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "create_symlink.py",
        description=(
            "创建或更新软链接。目标已存在时：\n"
            "  - 若为软链接且指向正确，直接返回成功；\n"
            "  - 若为软链接但指向错误，删除后重建；\n"
            "  - 若为实体文件/目录，删除后重建。"
        ),
        add_help=False,
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("source", metavar="<源目录>", help="源目录（必须存在）")
    parser.add_argument("target", metavar="<目标目录>", help="目标软链接路径")
    return parser


def resolve_source(source: str):
    """返回源的绝对路径；不存在或不可访问时返回 None。

    支持文件和目录（原版要求源必须是目录）。
    """
    if not os.path.exists(source):
        return None
    try:
        return os.path.realpath(source)
    except OSError:
        return None

def resolve_target(target: str):
    """返回目标的绝对路径；父目录不可访问时返回 None。"""
    parent = os.path.dirname(target) or "."
    if not os.path.isdir(parent):
        return None
    try:
        return os.path.join(os.path.realpath(parent), os.path.basename(target))
    except OSError:
        return None


def remove_path(path: str) -> None:
    """删除文件、软链接或目录。"""
    if os.path.islink(path) or not os.path.isdir(path):
        os.remove(path)
    else:
        shutil.rmtree(path)


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # 1. 解析源路径
    source_abs = resolve_source(args.source)
    if source_abs is None:
        print(f"[FAIL] 源不存在或不可访问: {args.source}", file=sys.stderr)
        return 1

    # 2. 解析目标绝对路径
    target_abs = resolve_target(args.target)
    if target_abs is None:
        print(f"[FAIL] 目标父目录不可访问: {args.target}", file=sys.stderr)
        return 1

    # 3. 检查目标是否已存在
    if os.path.islink(target_abs):
        current_source = os.path.realpath(target_abs)
        if current_source == source_abs:
            print(
                f"[SUCCESS] 软链接已存在且指向正确: "
                f"{target_abs} -> {source_abs}"
            )
            return 0
        print(
            f"[INFO] 软链接指向错误，正在删除旧链接: "
            f"{target_abs} -> {current_source}"
        )
        os.remove(target_abs)
    elif os.path.exists(target_abs):
        print(f"[WARN] 目标是一个实体文件/目录，正在删除: {target_abs}")
        remove_path(target_abs)

    # 4. 确保目标父目录存在
    os.makedirs(os.path.dirname(target_abs) or ".", exist_ok=True)

    # 5. 创建软链接
    try:
        os.symlink(source_abs, target_abs)
    except OSError as exc:
        print(f"[FAIL] 软链接创建失败: {exc}", file=sys.stderr)
        return 1

    print(f"[SUCCESS] 软链接创建成功: {target_abs} -> {source_abs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())