#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
以软链接方式安装 hermes-agent 可执行文件（支持 default 与指定 profile）。

用法:
    ./symlink_install_bin.py -help
    ./symlink_install_bin.py <bin>
    ./symlink_install_bin.py <bin> [profile]

源:
    $HOME/Public/external_bin/<bin>   （文件或目录均可）

目标:
    default: $HOME/.hermes/bin/<bin>
    profile: $HOME/.hermes/profiles/<name>/bin/<bin>

软链接通过 file/create_symlink.py 创建。

返回值:
    0 = 成功
    1 = 失败
"""

import argparse
import os
import subprocess
import sys


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser():
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "symlink_install_bin.py",
        description=(
            "以软链接方式安装 hermes-agent 可执行文件。\n"
            "default: $HOME/.hermes/bin/<bin>\n"
            "profile: $HOME/.hermes/profiles/<name>/bin/<bin>\n"
            "源可以是文件或目录；软链接由 file/create_symlink.py 创建。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("bin", metavar="<bin>", help="可执行文件/目录名（悬空软链接视为不存在，会被拒绝）")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="Profile 名称；省略或传 default 表示主 default profile")
    parser.add_argument("--source-dir", metavar="<dir>", default=None,
                        help="源目录根（默认 $HOME/Public/external_bin）")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根目录（默认 $HOME/.hermes）")
    parser.add_argument("--create-symlink", metavar="<path>", default=None,
                        help="create_symlink.py 路径（默认探测 file/create_symlink.py）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划")
    return parser


def resolve_create_symlink(override):
    if override:
        return os.path.abspath(os.path.expanduser(override))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "file", "create_symlink.py"),
        os.path.join(script_dir, os.pardir, "file", "create_symlink.py"),
        os.path.join(script_dir, "create_symlink.py"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return os.path.abspath(path)
    return os.path.abspath(candidates[1])


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
    print(f">> 目标链接: {target}")

    if not (os.path.isfile(src) or os.path.isdir(src)):
        print(f"[FAIL] 源不存在: {src}", file=sys.stderr)
        return 1

    create_py = resolve_create_symlink(args.create_symlink)
    if not os.path.isfile(create_py):
        print(f"[FAIL] 找不到 create_symlink.py: {create_py}", file=sys.stderr)
        print("提示：可用 --create-symlink 指定其路径", file=sys.stderr)
        return 1

    if not args.dry_run:
        try:
            os.makedirs(os.path.dirname(target), exist_ok=True)
        except OSError as exc:
            print(f"[FAIL] 创建目标父目录失败: {exc}", file=sys.stderr)
            return 1

    cmd = [sys.executable, create_py, src, target]
    print(">> 执行命令: " + " ".join(cmd))
    if args.dry_run:
        print("   [dry-run] 未执行")
        return 0
    try:
        rc = subprocess.run(cmd).returncode
    except OSError as exc:
        print(f"[FAIL] 执行失败: {exc}", file=sys.stderr)
        return 1
    if rc != 0:
        print("[FAIL] 创建软链接失败", file=sys.stderr)
        return 1

    print(f"✅ 软链接已创建: {target} -> {src}")
    return 0


if __name__ == "__main__":
    sys.exit(main())