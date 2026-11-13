#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行插件的额外初始化脚本。

用法:
    ./init_plugin.py -help
    ./init_plugin.py <plugin> <sh_path> [profile]

示例:
    ./init_plugin.py hermes-lcm ./scripts/install.sh          # 默认 default
    ./init_plugin.py hermes-lcm ./scripts/install.sh ceo      # profile=ceo

目标目录:
    全局:    $HOME/.hermes/plugins/<plugin>
    Profile: $HOME/.hermes/profiles/<profile>/plugins/<plugin>

注意:
    sh_path 会先切换到目标目录后再解析，因此相对路径（如 ./scripts/install.sh）
    是相对“目标目录”的，与 Bash 版 cd "$TARGET_DIR" 的行为一致；
    也支持绝对路径。

返回值:
    0 = 成功（含脚本未找到而跳过）
    1 = 失败
"""

import argparse
import os
import subprocess
import sys


class _ArgumentParser(argparse.ArgumentParser):
    """参数错误时返回码为 1，与脚本语义保持一致。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "init_plugin.py",
        description=(
            "在容器内部执行插件的额外初始化脚本。\n"
            "执行前会切换到插件目标目录（全局或 profile 下）。\n"
            "sh_path 为相对路径时相对目标目录解析，也可传入绝对路径。\n"
            "若脚本不存在，则输出警告并跳过（返回 0）。"
        ),
        add_help=False,
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("plugin", metavar="<plugin>",
                        help="插件名称，例如 hermes-lcm")
    parser.add_argument("sh_path", metavar="<sh_path>",
                        help="初始化脚本路径（相对目标目录或绝对路径）")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="可选的 Agent Profile 名称；省略时操作全局插件")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    plugin = args.plugin
    sh_path = args.sh_path
    profile = args.profile

    hermes_home = os.path.join(os.path.expanduser("~"), ".hermes")

    # 1. 动态确定目标目录
    if profile:
        target_dir = os.path.join(
            hermes_home, "profiles", profile, "plugins", plugin
        )
        print(f">> 模式: Profile [{profile}]")
    else:
        target_dir = os.path.join(hermes_home, "plugins", plugin)
        print(">> 模式: Global Default")

    print(f">> 目标目录: {target_dir}")

    # 2. 前置检查：目标目录必须存在
    if not os.path.isdir(target_dir):
        print(f"[FAIL] 目标目录不存在: {target_dir}", file=sys.stderr)
        print("提示：请先使用 copy_install_plugin.py 部署插件",
              file=sys.stderr)
        return 1

    # 3. 解析脚本路径（相对路径基于目标目录解析）
    resolved = sh_path if os.path.isabs(sh_path) \
        else os.path.join(target_dir, sh_path)

    if not os.path.isfile(resolved):
        print(f">> 警告: 未找到 {sh_path}（解析为 {resolved}），跳过。")
        return 0

    # 4. 加可执行位（等价 chmod +x）
    try:
        mode = os.stat(resolved).st_mode
        os.chmod(resolved, mode | 0o111)
    except OSError as exc:
        print(f"[WARN] 无法 chmod: {exc}", file=sys.stderr)

    # 5. 执行初始化脚本
    #    等价于原脚本的：cd "$TARGET_DIR" && eval $SH_PATH
    #    使用 shell=True + cwd=target_dir，既保持相对路径语义，
    #    也兼容 sh_path 中带参数/命令（如 "bash ./scripts/install.sh"）。
    print(f">> 执行 {sh_path} ...")
    try:
        result = subprocess.run(sh_path, shell=True, cwd=target_dir)
    except OSError as exc:
        print(f"[FAIL] 执行失败: {exc}", file=sys.stderr)
        return 1

    if result.returncode != 0:
        print(f"[FAIL] 脚本执行失败 (exit {result.returncode})",
              file=sys.stderr)
        return 1

    print(">> 安装脚本执行完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())