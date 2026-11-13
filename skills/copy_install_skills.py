#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
以复制方式安装 hermes-agent 技能（支持 default 主 profile 与指定 profile）。

用法:
    ./copy_install_skills.py -help
    ./copy_install_skills.py <skill> [profile]

路径约定:
    default 主 profile : $HOME/.hermes/skills/<skill>
    其它 profile       : $HOME/.hermes/profiles/<name>/skills/<skill>

说明:
    Skills 安装后自动作为斜杠命令可用，无需 enable 步骤。
    目标已存在时先删除再复制；软链接只删链接本身。
    复制时保留符号链接（symlinks=True），与 `cp -rf` 一致。

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


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "copy_install_skills.py",
        description=(
            "以复制方式安装 hermes-agent 技能。\n"
            "default 主 profile: $HOME/.hermes/skills/<skill>\n"
            "命名 profile:       $HOME/.hermes/profiles/<name>/skills/<skill>\n"
            "目标已存在时先删除再复制；软链接只删链接本身。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("skill", metavar="<skill>", help="技能名称")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="Profile 名称；省略或传 default 表示主 default profile")
    parser.add_argument("--source-dir", metavar="<dir>", default=None,
                        help="源目录根（默认 $HOME/Public/external_skills）")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根目录（默认 $HOME/.hermes）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划")
    return parser


def resolve_target(skill, profile, hermes_home):
    if profile is None or profile == "default":
        return os.path.join(hermes_home, "skills", skill), True
    return os.path.join(hermes_home, "profiles", profile, "skills", skill), False


def purge(path):
    """删除文件/软链接/目录（软链接只删链接本身）。"""
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
        print("[dry-run] 将删除目标（软链接只删链接本身）并复制源（保留符号链接）")
        return 0

    if os.path.lexists(target):
        print(f"[WARN] 目标已存在，正在删除: {target}")
        # 修复 P3：purge 失败时给出明确错误，而不是冒泡成“复制失败”
        try:
            purge(target)
        except OSError as exc:
            print(f"[FAIL] 删除目标失败: {exc}", file=sys.stderr)
            return 1

    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        # 修复 P2：保留源目录内的符号链接
        shutil.copytree(source, target, dirs_exist_ok=False, symlinks=True)
    except Exception as exc:
        print(f"[FAIL] 复制失败: {exc}", file=sys.stderr)
        return 1

    print(f"✅ 技能已安装: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())