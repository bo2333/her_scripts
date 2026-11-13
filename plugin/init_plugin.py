#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行插件的额外初始化脚本。

用法:
    ./init_plugin.py -help
    ./init_plugin.py <plugin> <script> [profile]

示例:
    ./init_plugin.py hermes-lcm ./scripts/install.sh          # 默认 default
    ./init_plugin.py hermes-lcm ./scripts/install.sh ceo      # profile=ceo
    ./init_plugin.py hermes-lcm "bash ./scripts/install.sh"   # 支持带参数

目标目录:
    default: $HOME/.hermes/plugins/<plugin>
    profile: $HOME/.hermes/profiles/<profile>/plugins/<plugin>

说明:
    script 会切换到目标目录后再解析：
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


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "init_plugin.py",
        description=(
            "在插件目标目录中执行初始化脚本。\n"
            "default 主 profile: $HOME/.hermes/plugins/<plugin>\n"
            "命名 profile:       $HOME/.hermes/profiles/<name>/plugins/<plugin>\n"
            "相对路径的 script 基于目标目录解析；支持带参数的命令。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("plugin", metavar="<plugin>", help="插件名称")
    parser.add_argument("script", metavar="<script>",
                        help="初始化脚本路径或命令（相对目标目录或绝对路径）")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="Profile 名称；省略或传 default 表示主 default profile")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根目录（默认 $HOME/.hermes）")
    return parser


def resolve_script(target_dir, script):
    """返回 (exists, resolved)。"""
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


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    plugin = args.plugin
    script = args.script
    raw_profile = args.profile
    is_default = raw_profile is None or raw_profile == "default"

    home = os.path.expanduser("~")
    hermes_home = (os.path.abspath(os.path.expanduser(args.hermes_home))
                   if args.hermes_home
                   else os.path.join(home, ".hermes"))

    if is_default:
        target_dir = os.path.join(hermes_home, "plugins", plugin)
        mode = "default"
    else:
        target_dir = os.path.join(hermes_home, "profiles", raw_profile, "plugins", plugin)
        mode = f"profile [{raw_profile}]"

    print(f">> 模式: {mode}")
    print(f">> 目标目录: {target_dir}")

    if not os.path.isdir(target_dir):
        print(f"[FAIL] 目标目录不存在: {target_dir}", file=sys.stderr)
        print("提示：请先使用 copy_install_plugin.py 或 symlink_install_plugin.py 安装",
              file=sys.stderr)
        return 1

    exists, resolved = resolve_script(target_dir, script)
    if not exists:
        print(f">> 警告: 未找到 {script}（解析为 {resolved}），跳过。")
        return 0

    if os.path.isfile(resolved):
        try:
            mode_bits = os.stat(resolved).st_mode
            os.chmod(resolved, mode_bits | 0o111)
        except OSError as exc:
            print(f"[WARN] chmod 失败: {exc}", file=sys.stderr)

    print(f">> 执行 {script} ...")
    try:
        rc = subprocess.run(script, shell=True, cwd=target_dir).returncode
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