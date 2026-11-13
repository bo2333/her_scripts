#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除（禁用并移除）hermes-agent 插件。

用法:
    ./clean_plugin.py -help
    ./clean_plugin.py <plugin> [profile]

示例:
    ./clean_plugin.py hermes-lcm            # 全局（default）
    ./clean_plugin.py hermes-lcm ceo        # profile=ceo
    ./clean_plugin.py hermes-lcm default    # 显式 default（等价于省略）

流程:
    1) hermes [-p <profile>] plugins disable <plugin>
    2) hermes [-p <profile>] plugins remove  <plugin>
    disable 失败即终止（与原 `&&` 语义一致）；--skip-disable 可跳过 disable。

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
        prog=os.path.basename(sys.argv[0]) or "clean_plugin.py",
        description=(
            "删除（禁用并移除）hermes-agent 插件。\n"
            "支持 default 主 profile 与指定 profile。\n"
            "执行顺序：\n"
            "  hermes [-p <profile>] plugins disable <plugin>\n"
            "  hermes [-p <profile>] plugins remove  <plugin>\n"
            "disable 失败即终止；--skip-disable 可跳过 disable。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("plugin", metavar="<plugin>", help="插件名称")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="Profile 名称；省略或传 default 表示主 default profile")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根目录（默认 $HOME/.hermes）")
    parser.add_argument("--skip-disable", action="store_true",
                        help="跳过 disable 步骤，直接 remove")
    parser.add_argument("--purge", action="store_true",
                        help="remove 成功后清理残留（软链接只删链接本身）")
    return parser


def run_cmd(cmd):
    print(f">> 执行命令: {' '.join(cmd)}")
    try:
        return subprocess.run(cmd).returncode
    except FileNotFoundError:
        print(f"[FAIL] 命令不存在: {cmd[0]}", file=sys.stderr)
        return None
    except OSError as exc:
        print(f"[FAIL] 执行失败: {exc}", file=sys.stderr)
        return None


def resolve_plugin_dir(plugin, profile, hermes_home):
    """修复 P1：default 字面值等同省略，避免落到 profiles/default。"""
    if profile is None or profile == "default":
        return os.path.join(hermes_home, "plugins", plugin)
    return os.path.join(hermes_home, "profiles", profile, "plugins", plugin)


def purge_path(path):
    if os.path.islink(path) or not os.path.isdir(path):
        os.remove(path)
    else:
        shutil.rmtree(path)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    plugin = args.plugin
    raw_profile = args.profile
    is_default = raw_profile is None or raw_profile == "default"

    home = os.path.expanduser("~")
    hermes_home = (os.path.abspath(os.path.expanduser(args.hermes_home))
                   if args.hermes_home
                   else os.path.join(home, ".hermes"))

    prefix = ["hermes"] if is_default else ["hermes", "-p", raw_profile]
    print(f">> 模式: {'default' if is_default else raw_profile}")

    if args.skip_disable:
        print(">> 跳过 disable 步骤")
    else:
        rc = run_cmd(prefix + ["plugins", "disable", plugin])
        if rc is None:
            return 1
        if rc != 0:
            print(f"[FAIL] 禁用插件失败 (exit {rc})", file=sys.stderr)
            print("提示：若插件已禁用/不存在，可加 --skip-disable 直接 remove",
                  file=sys.stderr)
            return 1

    rc = run_cmd(prefix + ["plugins", "remove", plugin])
    if rc is None:
        return 1
    if rc != 0:
        print(f"[FAIL] 移除插件失败 (exit {rc})", file=sys.stderr)
        return 1

    if args.purge:
        target = resolve_plugin_dir(plugin, raw_profile, hermes_home)
        if os.path.lexists(target):
            print(f">> 清理残留: {target}")
            try:
                purge_path(target)
            except OSError as exc:
                print(f"[WARN] 清理残留失败: {exc}", file=sys.stderr)
        else:
            print(f">> 目录已不存在，无需清理: {target}")

    bar = "=" * 66
    print(bar)
    print("✅ 插件删除完成！")
    print(f"   Profile: {'default' if is_default else raw_profile}")
    print(f"   Plugin:  {plugin}")
    print(bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())