#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
以复制方式安装 hermes-agent 可执行文件（支持 default 与指定 profile）。

用法:
    ./copy_install_bin.py -help
    ./copy_install_bin.py <bin>
    ./copy_install_bin.py <bin> [profile]

源:
    $HOME/Public/external_bin/<bin>   （文件或目录均可）

目标:
    default: $HOME/.hermes/bin/<bin>
    profile: $HOME/.hermes/profiles/<name>/bin/<bin>

行为:
    - 源是文件: shutil.copy2 复制并保留权限（含可执行位）
    - 源是目录: 先删除目标（软链接只删链接本身），再 copytree（保留符号链接和权限）

返回值:
    0 = 成功
    1 = 失败
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
        prog=os.path.basename(sys.argv[0]) or "copy_install_bin.py",
        description=(
            "以复制方式安装 hermes-agent 可执行文件。\n"
            "default: $HOME/.hermes/bin/<bin>\n"
            "profile: $HOME/.hermes/profiles/<name>/bin/<bin>\n"
            "源可以是文件或目录；复制保留权限（含可执行位）与符号链接。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("bin", metavar="<bin>", help="可执行文件/目录名")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="Profile 名称；省略或传 default 表示主 default profile")
    parser.add_argument("--source-dir", metavar="<dir>", default=None,
                        help="源目录根（默认 $HOME/Public/external_bin）")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根目录（默认 $HOME/.hermes）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划")
    return parser


def purge(path):
    """删除文件/软链接/目录（软链接只删链接本身）。"""
    if os.path.islink(path) or not os.path.isdir(path):
        os.remove(path)
    else:
        shutil.rmtree(path)


def main(argv=None):
    args = build_parser().parse_args(argv)
    raw_profile = args.profile
    is_default = raw_profile is None or raw_profile == "default"

    home = os.path.expanduser("~")
    source_root = (os.path.abspath(os.path.expanduser(args.source_dir))
                   if args.source_dir
                   else os.path.join(home, "Public", "external_bin"))
    hermes_home = (os.path.abspath(os.path.expanduser(args.hermes_home))
                   if args.hermes_home
                   else os.path.join(home, ".hermes"))
    src = os.path.join(source_root, args.bin)

    if is_default:
        target = os.path.join(hermes_home, "bin", args.bin)
        mode = "default"
    else:
        target = os.path.join(hermes_home, "profiles", raw_profile, "bin", args.bin)
        mode = f"profile [{raw_profile}]"

    print(f">> 模式: {mode}")
    print(f">> 源:   {src}")
    print(f">> 目标: {target}")

    if not (os.path.isfile(src) or os.path.isdir(src)):
        print(f"[FAIL] 源不存在: {src}", file=sys.stderr)
        return 1

    if args.dry_run:
        kind = "文件" if os.path.isfile(src) else "目录"
        print(f">> [dry-run] 将移除目标（如有）并复制{kind}")
        return 0

    # 1. 移除已有目标（软链接只删链接本身，不跟随）
    if os.path.lexists(target):
        print(f"[WARN] 目标已存在，正在删除: {target}")
        try:
            purge(target)
        except OSError as exc:
            print(f"[FAIL] 删除目标失败: {exc}", file=sys.stderr)
            return 1

    # 2. 创建目标父目录
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
    except OSError as exc:
        print(f"[FAIL] 创建目标父目录失败: {exc}", file=sys.stderr)
        return 1

    # 3. 复制
    try:
        if os.path.isfile(src):
            shutil.copy2(src, target)          # copy2 保留权限位（含可执行）
        else:
            shutil.copytree(src, target, symlinks=True)
    except Exception as exc:
        print(f"[FAIL] 复制失败: {exc}", file=sys.stderr)
        return 1

    print(f"✅ 已安装: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())