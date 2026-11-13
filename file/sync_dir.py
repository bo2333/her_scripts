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
    - target 是目录：按 rsync -a --delete --exclude 的语义同步
    - 优先 rsync -av --delete；无 rsync 时用 Python 兜底（语义与 rsync 一致）
    - exclude 按 basename 匹配任意层级，且目标端已有的同名 exclude 项不会被删除

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
            "优先使用 rsync -av --delete；无 rsync 时用 Python 兜底，\n"
            "两者对 exclude 的语义一致：按 basename 匹配任意层级，\n"
            "且目标端已有的同名 exclude 项不会被删除。"
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
# Python 兜底实现（语义对齐 rsync -a --delete --exclude）
# ---------------------------------------------------------------------------

def _sync_tree(src: str, dst: str, exclude: set) -> None:
    """递归同步 src → dst，行为尽量匹配 rsync -a --delete --exclude。

    规则:
      - 源中有、目标中无：复制/创建
      - 源和目标都有：更新（目录递归，文件/链接覆盖）
      - 源中无、目标中有：删除（除非 basename 在 exclude 中）
      - basename 在 exclude 中：双向跳过（不复制也不删除）
      - 源端软链接：按链接本身复制（不跟随），避免链接循环
    """
    # 目标端若是文件/软链接，先清掉，让后续能创建目录
    if os.path.lexists(dst) and (os.path.islink(dst) or not os.path.isdir(dst)):
        os.remove(dst)
    os.makedirs(dst, exist_ok=True)

    # 1. 复制/更新源内容到目标
    for entry in os.listdir(src):
        if entry in exclude:
            continue
        s = os.path.join(src, entry)
        d = os.path.join(dst, entry)

        if os.path.isdir(s) and not os.path.islink(s):
            _sync_tree(s, d, exclude)
            continue

        # 源是文件或软链接：先清掉目标端已有项（类型可能不同）
        if os.path.lexists(d):
            if os.path.islink(d) or not os.path.isdir(d):
                os.remove(d)
            else:
                shutil.rmtree(d)
        if os.path.islink(s):
            os.symlink(os.readlink(s), d)
        else:
            shutil.copy2(s, d)

    # 2. 删除目标端源没有的项（排除 exclude）
    for entry in os.listdir(dst):
        if entry in exclude:
            continue
        d = os.path.join(dst, entry)
        s = os.path.join(src, entry)
        if not os.path.lexists(s):
            if os.path.islink(d) or not os.path.isdir(d):
                os.remove(d)
            else:
                shutil.rmtree(d)


def sync_with_python(src: str, dst: str, exclude: list) -> bool:
    try:
        _sync_tree(src, dst, set(exclude))
        return True
    except Exception as exc:
        print(f"[FAIL] 同步失败: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# rsync 实现
# ---------------------------------------------------------------------------

def sync_with_rsync(src: str, dst: str, exclude: list) -> bool:
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