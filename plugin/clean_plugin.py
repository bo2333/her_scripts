#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除（禁用并移除）hermes-agent 插件。

用法:
    ./clean_plugin.py -help
    ./clean_plugin.py <plugin>
    ./clean_plugin.py <plugin> <profile>

示例:
    ./clean_plugin.py hermes-lcm            # 删除全局（default）插件
    ./clean_plugin.py hermes-lcm ceo        # 删除 profile=ceo 的插件

流程:
    1) hermes [-p <profile>] plugins disable <plugin>
    2) hermes [-p <profile>] plugins remove  <plugin>

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
    """参数错误时返回码为 1，与脚本语义保持一致。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "clean_plugin.py",
        description=(
            "删除（禁用并移除）hermes-agent 插件。\n"
            "默认操作全局（default agent）插件；指定 profile 后操作该 profile 下的插件。\n"
            "执行顺序：\n"
            "  hermes [-p <profile>] plugins disable <plugin>\n"
            "  hermes [-p <profile>] plugins remove  <plugin>\n"
            "其中 disable 成功后才执行 remove（与原脚本 `&&` 语义一致）；\n"
            "若插件已禁用/残留，可用 --skip-disable 直接执行 remove。"
        ),
        add_help=False,
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("plugin", metavar="<plugin>",
                        help="插件名称，例如 hermes-lcm")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="可选的 Agent Profile 名称；省略时操作全局插件")
    parser.add_argument("--skip-disable", action="store_true",
                        help="跳过 disable 步骤，直接执行 remove（适用于插件已禁用/残留场景）")
    parser.add_argument("--purge", action="store_true",
                        help="remove 成功后，若插件目录仍残留则一并删除")
    return parser


def run_cmd(cmd) -> int | None:
    """执行命令，返回 returncode；无法执行时返回 None。"""
    print(f">> 执行命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except FileNotFoundError:
        print(f"[FAIL] 命令不存在: {cmd[0]}", file=sys.stderr)
        return None
    except OSError as exc:
        print(f"[FAIL] 执行失败: {exc}", file=sys.stderr)
        return None


def resolve_plugin_dir(plugin: str, profile: str | None) -> str:
    """返回插件在磁盘上的默认目录（与 copy_install_plugin 的部署路径一致）。"""
    home = os.path.expanduser("~")
    if profile:
        return os.path.join(home, ".hermes", "profiles", profile,
                            "plugins", plugin)
    return os.path.join(home, ".hermes", "plugins", plugin)


def purge_dir(path: str) -> None:
    """删除目录/文件/软链接（含损坏软链）。"""
    if os.path.islink(path) or not os.path.isdir(path):
        os.remove(path)
    else:
        shutil.rmtree(path)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    plugin = args.plugin
    profile = args.profile

    # 构建命令前缀
    if profile:
        prefix = ["hermes", "-p", profile]
        print(f">> 模式: Profile [{profile}]")
    else:
        prefix = ["hermes"]
        print(">> 模式: Global Default")

    # 1) disable
    if args.skip_disable:
        print(">> 跳过 disable 步骤")
    else:
        rc = run_cmd(prefix + ["plugins", "disable", plugin])
        if rc is None:
            return 1
        if rc != 0:
            print(f"[FAIL] 禁用插件失败 (exit {rc})", file=sys.stderr)
            print("提示：若插件已禁用/不存在，可加 --skip-disable 直接执行 remove",
                  file=sys.stderr)
            return 1

    # 2) remove
    rc = run_cmd(prefix + ["plugins", "remove", plugin])
    if rc is None:
        return 1
    if rc != 0:
        print(f"[FAIL] 移除插件失败 (exit {rc})", file=sys.stderr)
        return 1

    # 3) 可选：清理残留目录
    if args.purge:
        plugin_dir = resolve_plugin_dir(plugin, profile)
        if os.path.exists(plugin_dir) or os.path.islink(plugin_dir):
            print(f">> 清理残留目录: {plugin_dir}")
            try:
                purge_dir(plugin_dir)
            except OSError as exc:
                print(f"[WARN] 清理残留目录失败: {exc}", file=sys.stderr)
        else:
            print(f">> 目录已不存在，无需清理: {plugin_dir}")

    # 4) 完成
    bar = "=" * 66
    print(bar)
    print("✅ 插件删除完成！")
    if profile:
        print(f"   Profile: {profile} {plugin}")
    else:
        print(f"   Global:  {plugin}")
    print(bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())