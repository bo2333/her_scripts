#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将源目录内容镜像同步到目标目录（通用工具）。

用法:
    ./sync_dir.py -help
    ./sync_dir.py <source> <target>
    ./sync_dir.py <source> <target> --exclude node_modules --exclude .git
    ./sync_dir.py <source> <target> --dry-run

行为:
    - target 是软链接：先移除链接本身（不跟随），再创建空目录
    - target 是普通文件：先删除，再创建空目录
    - target 是目录：清空内容（保留名为 exclude 的顶层项，模拟 rsync --delete --exclude）后同步
    - 优先 rsync -av --delete；无 rsync 时用 Python 兜底
    - exclude 按 basename 匹配，作用于源里任意层级

返回值:
    0 = 成功
    1 = 失败
"""

import argparse
import os
import shutil
import subprocess
import sys


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "sync_dir.py",
        description=(
            "将源目录内容镜像同步到目标目录。\n"
            "目标为软链接/普通文件时先移除，再创建空目录后同步。\n"
            "优先使用 rsync -av --delete；无 rsync 时用 Python 兜底。\n"
            "exclude 按 basename 匹配源里任意层级（同 rsync --exclude）。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("source", metavar="<source>", help="源目录（必须存在）")
    parser.add_argument("target", metavar="<target>", help="目标目录")
    parser.add_argument("--exclude", metavar="<name>", action="append", default=[],
                        help="排除的名称（可多次指定），如 --exclude node_modules")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划")
    return parser


# ---------------------------------------------------------------------------
# Python 兜底实现
# ---------------------------------------------------------------------------

def _clear_dir_preserving(dst, exclude):
    """清空 dst 内容，保留顶层名为 exclude 的条目（模拟 rsync --delete --exclude）。"""
    for entry in os.listdir(dst):
        if entry in exclude:
            continue
        path = os.path.join(dst, entry)
        if os.path.islink(path) or not os.path.isdir(path):
            os.remove(path)
        else:
            shutil.rmtree(path)


def _copy_contents(src, dst, exclude):
    ignore = shutil.ignore_patterns(*exclude) if exclude else None
    for entry in os.listdir(src):
        if entry in exclude:
            continue
        s = os.path.join(src, entry)
        d = os.path.join(dst, entry)
        if os.path.isdir(s) and not os.path.islink(s):
            shutil.copytree(s, d, ignore=ignore, dirs_exist_ok=True)
        else:
            # 保留符号链接本身，不解引用
            shutil.copy2(s, d, follow_symlinks=False)


def sync_with_python(src, dst, exclude):
    try:
        _clear_dir_preserving(dst, set(exclude))
        _copy_contents(src, dst, set(exclude))
        return True
    except Exception as exc:
        print(f"[FAIL] 同步失败: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# rsync 实现
# ---------------------------------------------------------------------------

def sync_with_rsync(src, dst, exclude):
    cmd = ["rsync", "-av", "--delete"]
    for e in exclude:
        cmd.append(f"--exclude={e}")
    cmd += [f"{src}/", f"{dst}/"]
    print(">> " + " ".join(cmd))
    try:
        return subprocess.run(cmd).returncode == 0
    except OSError as exc:
        print(f"[WARN] rsync 失败: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    src = os.path.abspath(os.path.expanduser(args.source))
    dst = os.path.abspath(os.path.expanduser(args.target))
    exclude = args.exclude

    if not os.path.isdir(src):
        print(f"[FAIL] 源目录不存在: {src}", file=sys.stderr)
        return 1

    print(f">> 源:   {src}")
    print(f">> 目标: {dst}")
    if exclude:
        print(f">> 排除: {', '.join(exclude)}")

    if args.dry_run:
        print(">> [dry-run] 未执行")
        return 0

    # 1) 目标本身是软链接：移除链接本身（不跟随）
    if os.path.islink(dst):
        print(f"[INFO] 目标是软链接，移除链接本身: {dst}")
        try:
            os.remove(dst)
        except OSError as exc:
            print(f"[FAIL] 移除软链接失败: {exc}", file=sys.stderr)
            return 1
    # 2) 目标是普通文件：删除
    elif os.path.exists(dst) and not os.path.isdir(dst):
        print(f"[WARN] 目标是普通文件，删除: {dst}")
        try:
            os.remove(dst)
        except OSError as exc:
            print(f"[FAIL] 删除目标文件失败: {exc}", file=sys.stderr)
            return 1

    # 3) 确保目标目录存在
    try:
        os.makedirs(dst, exist_ok=True)
    except OSError as exc:
        print(f"[FAIL] 创建目标目录失败: {exc}", file=sys.stderr)
        return 1

    # 4) 同步
    if shutil.which("rsync"):
        print(">> 使用 rsync 同步...")
        ok = sync_with_rsync(src, dst, exclude)
    else:
        print(">> 使用 Python 同步...")
        ok = sync_with_python(src, dst, exclude)

    if not ok:
        print("[FAIL] 同步失败", file=sys.stderr)
        return 1

    print("✅ 同步完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())