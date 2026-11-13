#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
以软链接方式安装 hermes-agent 技能（支持 default 与指定 profile）。

用法:
    ./symlink_install_skills.py -help
    ./symlink_install_skills.py <skill>
    ./symlink_install_skills.py <skill> [profile]

路径:
    default: $HOME/.hermes/skills/<skill>          -> 源目录
    profile: $HOME/.hermes/profiles/<name>/skills/<skill> -> 源目录

软链接通过 create_symlink.py 创建；技能安装后自动可用。
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
        prog=os.path.basename(sys.argv[0]) or "symlink_install_skills.py",
        description=(
            "以软链接方式安装 hermes-agent 技能。\n"
            "default 主 profile: $HOME/.hermes/skills/<skill>\n"
            "命名 profile:       $HOME/.hermes/profiles/<name>/skills/<skill>\n"
            "软链接通过 create_symlink.py 创建。"
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
    parser.add_argument("--create-symlink", metavar="<path>", default=None,
                        help="create_symlink.py 路径")
    parser.add_argument("--dry-run", action="store_true", help="仅打印计划")
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
    for c in candidates:
        if os.path.isfile(c):
            return os.path.abspath(c)
    return os.path.abspath(candidates[1])


def resolve_target(skill, profile, hermes_home):
    if profile is None or profile == "default":
        return os.path.join(hermes_home, "skills", skill), True
    return os.path.join(hermes_home, "profiles", profile, "skills", skill), False


def run(cmd, dry_run=False):
    print(">> " + " ".join(cmd))
    if dry_run:
        print("   [dry-run] 未执行")
        return 0
    try:
        return subprocess.run(cmd).returncode
    except OSError as exc:
        print(f"[FAIL] 执行失败: {exc}", file=sys.stderr)
        return None


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
    print(f">> 目标链接: {target}")
    print(f">> 模式: {'default' if is_default else args.profile}")

    if not os.path.isdir(source):
        print(f"[FAIL] 源目录不存在: {source}", file=sys.stderr)
        return 1

    create_py = resolve_create_symlink(args.create_symlink)
    if not os.path.isfile(create_py):
        print(f"[FAIL] 找不到 create_symlink.py: {create_py}", file=sys.stderr)
        return 1

    if not args.dry_run:
        os.makedirs(os.path.dirname(target), exist_ok=True)

    rc = run([sys.executable, create_py, source, target], args.dry_run)
    if rc is None or rc != 0:
        print("[FAIL] 创建软链接失败", file=sys.stderr)
        return 1

    print(f"✅ 技能软链接已创建: {target} -> {source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())