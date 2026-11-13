#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卸载 hermes-agent 技能。

用法:
    ./clean_skills.py -help
    ./clean_skills.py <skill>
    ./clean_skills.py <skill> [profile]

命令:
    hermes [-p <profile>] skills uninstall <skill>

说明:
    Skills 没有 disable/enable 概念，卸载直接使用 uninstall。
    可选 --purge 清理残留目录。
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


def build_parser():
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
    parser.add_argument("-help", action="help", help="显示帮助并退出")
    parser.add_argument("skill", metavar="<skill>", help="技能名称")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="profile 名；省略或 default 表示主 default")
    parser.add_argument("--purge", action="store_true",
                        help="uninstall 后清理残留目录")
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


def resolve_dir(skill, profile, hermes_home):
    if profile is None or profile == "default":
        return os.path.join(hermes_home, "skills", skill)
    return os.path.join(hermes_home, "profiles", profile, "skills", skill)


def purge(path):
    if os.path.islink(path) or not os.path.isdir(path):
        os.remove(path)
    else:
        shutil.rmtree(path)


def main(argv=None):
    args = build_parser().parse_args(argv)
    home = os.path.expanduser("~")
    hermes_home = os.path.join(home, ".hermes")

    if args.profile is None or args.profile == "default":
        prefix = ["hermes"]
        mode = "default"
    else:
        prefix = ["hermes", "-p", args.profile]
        mode = f"profile [{args.profile}]"

    print(f">> 模式: {mode}")

    rc = run_cmd(prefix + ["skills", "uninstall", args.skill])
    if rc is None or rc != 0:
        print(f"[FAIL] 卸载失败 (exit {rc})", file=sys.stderr)
        return 1

    if args.purge:
        target = resolve_dir(args.skill, args.profile, hermes_home)
        if os.path.lexists(target):
            print(f">> 清理残留: {target}")
            try:
                purge(target)
            except OSError as exc:
                print(f"[WARN] 清理失败: {exc}", file=sys.stderr)

    print(f"✅ 技能已卸载: {args.skill}")
    return 0


if __name__ == "__main__":
    sys.exit(main())