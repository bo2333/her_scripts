#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
以复制方式安装 hermes-agent 技能（支持 default 主 profile 与指定 profile）。

用法:
    ./copy_install_skills.py -help
    ./copy_install_skills.py <skill>
    ./copy_install_skills.py <skill> [profile]

路径约定:
    default 主 profile : $HOME/.hermes/skills/<skill>
    其它 profile       : $HOME/.hermes/profiles/<name>/skills/<skill>

说明:
    Skills 安装后自动作为斜杠命令可用，无需 enable 步骤。
    若目标已存在，会先删除再复制（与 copy_install_plugin.py 一致）。
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
        prog=os.path.basename(sys.argv[0]) or "copy_install_skills.py",
        description=(
            "以复制方式安装 hermes-agent 技能。\n"
            "default 主 profile: $HOME/.hermes/skills/<skill>\n"
            "命名 profile:       $HOME/.hermes/profiles/<name>/skills/<skill>\n"
            "技能安装后自动可用，无需显式启用。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示帮助并退出")
    parser.add_argument("skill", metavar="<skill>", help="技能名称")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="profile 名；省略或 default 表示主 default")
    parser.add_argument("--source-dir", metavar="<dir>", default=None,
                        help="源根目录（默认 $HOME/Public/external_skills）")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根（默认 $HOME/.hermes）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印计划")
    return parser


def resolve_target(skill, profile, hermes_home):
    if profile is None or profile == "default":
        return os.path.join(hermes_home, "skills", skill), True
    return os.path.join(hermes_home, "profiles", profile, "skills", skill), False


def purge(path):
    if os.path.islink(path) or not os.path.isdir(path):
        os.remove(path)
    else:
        shutil.rmtree(path)


def main(argv=None):
    args = build_parser().parse_args(argv)
    home = os.path.expanduser("~")
    source_root = (os.path.abspath(os.path.expanduser(args.source_dir))
                   if args.source_dir
                   else os.path.join(home, "Public", "external_skills"))
    hermes_home = (os.path.abspath(os.path.expanduser(args.hermes_home))
                   if args.hermes_home
                   else os.path.join(home, ".hermes"))
    source = os.path.join(source_root, args.skill)
    target, is_default = resolve_target(args.skill, args.profile, hermes_home)

    print(f">> 源: {source}")
    print(f">> 目标: {target}")
    print(f">> 模式: {'default' if is_default else args.profile}")

    if not os.path.isdir(source):
        print(f"[FAIL] 源目录不存在: {source}", file=sys.stderr)
        return 1

    if args.dry_run:
        print("[dry-run] 将删除目标并复制源")
        return 0

    if os.path.lexists(target):
        print(f"[WARN] 目标已存在，正在删除: {target}")
        purge(target)

    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copytree(source, target, dirs_exist_ok=False)
    except Exception as exc:
        print(f"[FAIL] 复制失败: {exc}", file=sys.stderr)
        return 1

    print(f"✅ 技能已安装: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())