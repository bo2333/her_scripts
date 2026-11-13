#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在技能目标目录中执行额外初始化脚本。

用法:
    ./init_skills.py -help
    ./init_skills.py <skill> <script> [profile]

路径:
    default: $HOME/.hermes/skills/<skill>
    profile: $HOME/.hermes/profiles/<name>/skills/<skill>

script 为相对路径时基于目标目录解析；支持绝对路径。
脚本不存在时警告并跳过（返回 0）。
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
        prog=os.path.basename(sys.argv[0]) or "init_skills.py",
        description=(
            "在技能目标目录中执行初始化脚本。\n"
            "default: $HOME/.hermes/skills/<skill>\n"
            "profile: $HOME/.hermes/profiles/<name>/skills/<skill>\n"
            "相对路径的 script 基于目标目录解析。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示帮助并退出")
    parser.add_argument("skill", metavar="<skill>", help="技能名称")
    parser.add_argument("script", metavar="<script>", help="初始化脚本路径")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="profile 名；省略或 default 表示主 default")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    home = os.path.expanduser("~")
    hermes_home = os.path.join(home, ".hermes")

    if args.profile is None or args.profile == "default":
        target = os.path.join(hermes_home, "skills", args.skill)
        mode = "default"
    else:
        target = os.path.join(hermes_home, "profiles", args.profile,
                              "skills", args.skill)
        mode = f"profile [{args.profile}]"

    print(f">> 模式: {mode}")
    print(f">> 目标目录: {target}")

    if not os.path.isdir(target):
        print(f"[FAIL] 目标目录不存在: {target}", file=sys.stderr)
        print("提示：请先使用 copy_install_skills.py 或 symlink_install_skills.py 安装",
              file=sys.stderr)
        return 1

    resolved = (args.script if os.path.isabs(args.script)
                else os.path.join(target, args.script))

    if not os.path.isfile(resolved):
        print(f">> 警告: 未找到 {args.script}（解析为 {resolved}），跳过。")
        return 0

    try:
        mode_bits = os.stat(resolved).st_mode
        os.chmod(resolved, mode_bits | 0o111)
    except OSError as exc:
        print(f"[WARN] chmod 失败: {exc}", file=sys.stderr)

    print(f">> 执行 {args.script} ...")
    try:
        rc = subprocess.run(args.script, shell=True, cwd=target).returncode
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