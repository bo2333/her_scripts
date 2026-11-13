#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在 bin 目录执行安装后初始化脚本（如 setcap、写入配置等）。

用法:
    ./init_bin.py -help
    ./init_bin.py <bin> <script> [profile]

目标目录:
    default: $HOME/.hermes/bin
    profile: $HOME/.hermes/profiles/<name>/bin

说明:
    script 在 bin 目标目录中执行（cwd=<bin 目录>）。
      - 第一个 token 含 '/' 或以 '.' 开头 → 视为路径，检查是否存在；
      - 否则视为命令名（在 PATH 中查找）。
    支持带参数的 shell 命令。脚本不存在时警告并跳过（返回 0）。

返回值:
    0 = 成功（含跳过）
    1 = 失败
"""

import argparse
import os
import shlex
import subprocess
import sys


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser():
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "init_bin.py",
        description=(
            "在 bin 目录中执行安装后初始化脚本。\n"
            "default: $HOME/.hermes/bin\n"
            "profile: $HOME/.hermes/profiles/<name>/bin\n"
            "script 可带参数；相对路径基于 bin 目录解析。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("bin", metavar="<bin>", help="可执行文件/目录名")
    parser.add_argument("script", metavar="<script>", help="初始化脚本路径或命令")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="Profile 名称；省略或传 default 表示主 default profile")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根目录（默认 $HOME/.hermes）")
    return parser


def resolve_script(target_dir, script):
    try:
        tokens = shlex.split(script)
    except ValueError:
        tokens = [script]
    if not tokens:
        return True, script
    first = tokens[0]
    if "/" in first or first.startswith("."):
        resolved = first if os.path.isabs(first) else os.path.join(target_dir, first)
        return os.path.isfile(resolved), resolved
    return True, first


def main(argv=None):
    args = build_parser().parse_args(argv)
    raw_profile = args.profile
    is_default = raw_profile is None or raw_profile == "default"

    home = os.path.expanduser("~")
    hermes_home = (os.path.abspath(os.path.expanduser(args.hermes_home))
                   if args.hermes_home
                   else os.path.join(home, ".hermes"))

    if is_default:
        bin_dir = os.path.join(hermes_home, "bin")
        mode = "default"
    else:
        bin_dir = os.path.join(hermes_home, "profiles", raw_profile, "bin")
        mode = f"profile [{raw_profile}]"
    target = os.path.join(bin_dir, args.bin)

    print(f">> 模式: {mode}")
    print(f">> bin 目录: {bin_dir}")
    print(f">> 目标: {target}")

    if not os.path.lexists(target):
        print(f"[FAIL] 目标不存在: {target}", file=sys.stderr)
        print("提示：请先使用 copy_install_bin.py 或 symlink_install_bin.py 安装",
              file=sys.stderr)
        return 1

    exists, resolved = resolve_script(bin_dir, args.script)
    if not exists:
        print(f">> 警告: 未找到 {args.script}（解析为 {resolved}），跳过。")
        return 0

    if os.path.isfile(resolved):
        try:
            mode_bits = os.stat(resolved).st_mode
            os.chmod(resolved, mode_bits | 0o111)
        except OSError as exc:
            print(f"[WARN] chmod 失败: {exc}", file=sys.stderr)

    print(f">> 执行 {args.script} ...")
    try:
        rc = subprocess.run(args.script, shell=True, cwd=bin_dir).returncode
    except OSError as exc:
        print(f"[FAIL] 执行失败: {exc}", file=sys.stderr)
        return 1

    if rc != 0:
        print(f"[FAIL] 脚本失败 (exit {rc})", file=sys.stderr)
        return 1

    print(">> 初始化脚本执行完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())