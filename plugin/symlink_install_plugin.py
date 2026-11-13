#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
以软链接方式安装 hermes-agent 插件（支持 default 主 profile 与指定 profile）。

用法:
    ./symlink_install_plugin.py -help
    ./symlink_install_plugin.py <plugin>
    ./symlink_install_plugin.py <plugin> [profile]

示例:
    ./symlink_install_plugin.py her_monitor_action_booth           # 默认主 default
    ./symlink_install_plugin.py her_monitor_action_booth ceo       # 部署到 profile=ceo
    ./symlink_install_plugin.py her_monitor_action_booth default   # 显式指定 default（等价于省略）

路径约定:
    default 主 profile : $HOME/.hermes
    其它 profile       : $HOME/.hermes/profiles/<name>

流程:
    1) 检查源目录: $HOME/Public/external_plugins/<plugin>
    2) 确定目标（软链接路径）:
         default: $HOME/.hermes/plugins/<plugin>
         profile: $HOME/.hermes/profiles/<profile>/plugins/<plugin>
    3) 创建目标父目录
    4) 调用 file/create_symlink.py 创建软链接：目标 -> 源
    5) hermes [-p <profile>] plugins enable <plugin>

返回值:
    0 = 成功
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
        prog=os.path.basename(sys.argv[0]) or "symlink_install_plugin.py",
        description=(
            "以软链接方式安装 hermes-agent 插件。\n"
            "支持 default 主 profile（$HOME/.hermes）与\n"
            "指定 profile（$HOME/.hermes/profiles/<name>）。\n"
            "软链接通过调用file/create_symlink.py 创建；\n"
            "默认安装后自动启用插件，可用 --no-enable 关闭。"
        ),
        add_help=False,
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("plugin", metavar="<plugin>",
                        help="插件名称，例如 hermes-lcm")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="可选的 Agent Profile 名称；省略或传 default 表示主 default profile")
    parser.add_argument("--source-dir", metavar="<dir>", default=None,
                        help="源目录根（默认 $HOME/Public/external_plugins）")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根目录（默认 $HOME/.hermes）；default profile 即此目录")
    parser.add_argument("--create-symlink", metavar="<path>", default=None,
                        help="create_symlink.py 路径（默认 <脚本目录>file/create_symlink.py）")
    parser.add_argument("--no-enable", action="store_true",
                        help="创建软链接后不自动启用插件")
    parser.add_argument("--dry-run", action="store_true",
                        help="只打印将要执行的操作，不做实际修改")
    return parser


def resolve_create_symlink(override: str | None) -> str:
    """返回 create_symlink.py 的绝对路径。

    依次探测以下候选（取第一个存在的）：
      1) <脚本目录>/file/create_symlink.py
      2) <脚本目录>/../file/create_symlink.py   ← 当前布局
      3) <脚本目录>/create_symlink.py
    若都不存在，返回候选 2 的路径（便于报错信息定位）。
    """
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
    # 都没找到时，返回最可能的候选（上一级 file/）用于报错提示
    return os.path.abspath(candidates[1])


def run(cmd, cwd=None, dry_run=False):
    """执行命令，返回 returncode；无法执行时返回 None。

    使用 sys.executable 调用 Python 脚本（无需目标脚本带可执行位）。
    """
    cmd_str = " ".join(cmd)
    if cwd:
        print(f">> 执行命令 (cwd={cwd}): {cmd_str}")
    else:
        print(f">> 执行命令: {cmd_str}")
    if dry_run:
        print("   [dry-run] 未实际执行")
        return 0
    try:
        return subprocess.run(cmd, cwd=cwd).returncode
    except FileNotFoundError:
        print(f"[FAIL] 命令不存在: {cmd[0]}", file=sys.stderr)
        return None
    except OSError as exc:
        print(f"[FAIL] 执行失败: {exc}", file=sys.stderr)
        return None


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    plugin = args.plugin
    raw_profile = args.profile

    # 规范化：省略 profile 或传 "default" 都视为 default 主 profile
    is_default = raw_profile is None or raw_profile == "default"
    profile_name = None if is_default else raw_profile

    home = os.path.expanduser("~")
    source_root = (
        os.path.abspath(os.path.expanduser(args.source_dir))
        if args.source_dir
        else os.path.join(home, "Public", "external_plugins")
    )
    hermes_home = (
        os.path.abspath(os.path.expanduser(args.hermes_home))
        if args.hermes_home
        else os.path.join(home, ".hermes")
    )

    source_dir = os.path.join(source_root, plugin)

    # 目标软链接路径 + 父目录 + 启用命令
    if is_default:
        target_dir = os.path.join(hermes_home, "plugins", plugin)
        target_parent = os.path.join(hermes_home, "plugins")
        enable_cmd = ["hermes", "plugins", "enable", plugin]
        mode_desc = "Global Default"
    else:
        target_dir = os.path.join(hermes_home, "profiles", profile_name, "plugins", plugin)
        target_parent = os.path.join(hermes_home, "profiles", profile_name, "plugins")
        enable_cmd = ["hermes", "-p", profile_name, "plugins", "enable", plugin]
        mode_desc = f"Profile [{profile_name}]"

    print(f">> 模式: {mode_desc}")
    print(f">> 源目录: {source_dir}")
    print(f">> 目标链接: {target_dir}")

    # 1. 源目录必须存在
    if not os.path.isdir(source_dir):
        print(f"[FAIL] 源目录不存在: {source_dir}", file=sys.stderr)
        print("提示：请确认插件代码已放在源目录，或用 --source-dir 指定",
              file=sys.stderr)
        return 1

    # 2. create_symlink.py 必须存在
    create_symlink_py = resolve_create_symlink(args.create_symlink)
    if not os.path.isfile(create_symlink_py):
        print(f"[FAIL] 找不到 create_symlink.py: {create_symlink_py}",
              file=sys.stderr)
        print("提示：可用 --create-symlink 指定其路径", file=sys.stderr)
        return 1

    # 3. 创建目标父目录（create_symlink.py 要求父目录已存在）
    if args.dry_run:
        print(f">> [dry-run] 将创建父目录: {target_parent}")
    else:
        try:
            os.makedirs(target_parent, exist_ok=True)
        except OSError as exc:
            print(f"[FAIL] 创建目标父目录失败: {exc}", file=sys.stderr)
            return 1

    # 4. 调用 create_symlink.py 创建软链接：target -> source
    rc = run([sys.executable, create_symlink_py, source_dir, target_dir],
             dry_run=args.dry_run)
    if rc is None:
        return 1
    if rc != 0:
        print(f"[FAIL] 创建软链接失败 (exit {rc})", file=sys.stderr)
        return 1

    # 5. 启用插件（默认启用；cwd 与 copy_install_plugin.py 保持一致）
    if args.no_enable:
        print(">> 跳过启用步骤（--no-enable）")
    else:
        rc = run(enable_cmd, cwd=target_dir, dry_run=args.dry_run)
        if rc is None:
            return 1
        if rc != 0:
            print(f"[FAIL] 启用插件失败 (exit {rc})", file=sys.stderr)
            print("提示：软链接已创建，可稍后手动启用", file=sys.stderr)
            return 1

    # 6. 完成
    bar = "=" * 66
    print(bar)
    print("✅ 软链接安装成功！")
    print(f"   链接: {target_dir}")
    print(f"   指向: {source_dir}")
    if is_default:
        print("   Profile: default")
    else:
        print(f"   Profile: {profile_name}")
    print(bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())