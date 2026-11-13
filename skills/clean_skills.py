#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卸载 hermes-agent 技能。

用法:
    ./clean_skills.py -help
    ./clean_skills.py <skill> [profile]

命令:
    hermes [-p <profile>] skills uninstall <skill>

说明:
    Skills 没有 disable/enable 概念，卸载直接使用 uninstall。
    --purge 清理残留（软链接只删链接本身）。

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
        prog=os.path.basename(sys.argv[0]) or "clean_skills.py",
        description=(
            "卸载 hermes-agent 技能。\n"
            "default: hermes skills uninstall <skill>\n"
            "profile: hermes -p <profile> skills uninstall <skill>"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("skill", metavar="<skill>", help="技能名称")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="Profile 名称；省略或传 default 表示主 default profile")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根目录（默认 $HOME/.hermes）")
    parser.add_argument("--purge", action="store_true",
                        help="uninstall 后清理残留（软链接只删链接本身）")
    return parser


def run_cmd(cmd):
    print(">> " + " ".join(cmd))
    try:
        return subprocess.run(cmd).returncode
    except FileNotFoundError:
        print(f"[FAIL] 命令不存在: {cmd[0]}", file=sys.stderr)
        return None
    except OSError as exc:
        print(f"[FAIL] 执行失败: {exc}", file=sys.stderr)
        return None


def resolve_target(skill, profile, hermes_home):
    """统一入口：返回 (path, is_default)，main 与 purge 共用，避免重复判断。"""
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
    hermes_home = (os.path.abspath(os.path.expanduser(args.hermes_home))
                   if args.hermes_home
                   else os.path.join(home, ".hermes"))

    target, is_default = resolve_target(args.skill, args.profile, hermes_home)
    prefix = ["hermes"] if is_default else ["hermes", "-p", args.profile]
    print(f">> 模式: {'default' if is_default else args.profile}")

    rc = run_cmd(prefix + ["skills", "uninstall", args.skill])
    if rc is None or rc != 0:
        print(f"[FAIL] 卸载失败 (exit {rc})", file=sys.stderr)
        return 1

    if args.purge:
        if os.path.lexists(target):
            print(f">> 清理残留: {target}")
            try:
                purge(target)
            except OSError as exc:
                print(f"[WARN] 清理失败: {exc}", file=sys.stderr)
        else:
            print(f">> 目录已不存在，无需清理: {target}")

    print(f"✅ 技能已卸载: {args.skill}")
    return 0


if __name__ == "__main__":
    sys.exit(main())