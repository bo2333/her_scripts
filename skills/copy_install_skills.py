#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
以复制方式安装 hermes-agent 技能。

用法:
    ./copy_install_skills.py -help
    ./copy_install_skills.py <skill> [profile]

路径约定:
    default: $HOME/.hermes/skills/<skill>
    profile: $HOME/.hermes/profiles/<name>/skills/<skill>

实现:
    目录同步逻辑由 file/sync_dir.py 提供，本脚本只负责计算路径并调用。
    Skills 安装后自动可用，无需 enable。

返回值:
    0 = 成功
    1 = 失败
"""

import argparse
import os
import subprocess
import sys


EXCLUDE = ["node_modules", ".git"]


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "copy_install_skills.py",
        description=(
            "以复制方式安装 hermes-agent 技能（排除 node_modules、.git）。\n"
            "default: $HOME/.hermes/skills/<skill>\n"
            "profile: $HOME/.hermes/profiles/<name>/skills/<skill>\n"
            "目录同步由 file/sync_dir.py 完成；技能安装后自动可用。"
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
    parser.add_argument("--sync-dir", metavar="<path>", default=None,
                        help="sync_dir.py 路径（默认自动探测 file/sync_dir.py）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划")
    return parser


def resolve_sync_dir(override: str | None) -> str:
    if override:
        return os.path.abspath(os.path.expanduser(override))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "file", "sync_dir.py"),
        os.path.join(script_dir, os.pardir, "file", "sync_dir.py"),
        os.path.join(script_dir, "sync_dir.py"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return os.path.abspath(path)
    return os.path.abspath(candidates[1])


def run_cmd(cmd, cwd=None) -> int | None:
    """执行命令，返回 returncode；无法执行时返回 None。

    区分 cwd 不存在与命令不存在两种 FileNotFoundError。
    """
    prefix = f">> 执行命令{' (cwd=' + cwd + ')' if cwd else ''}: "
    print(prefix + " ".join(cmd))
    try:
        return subprocess.run(cmd, cwd=cwd).returncode
    except FileNotFoundError:
        if cwd and not os.path.isdir(cwd):
            print(f"[FAIL] 工作目录不存在: {cwd}", file=sys.stderr)
        else:
            print(f"[FAIL] 命令不存在: {cmd[0]}", file=sys.stderr)
        return None
    except OSError as exc:
        print(f"[FAIL] 执行失败: {exc}", file=sys.stderr)
        return None


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    raw_profile = args.profile
    is_default = raw_profile is None or raw_profile == "default"

    home = os.path.expanduser("~")
    source_root = (os.path.abspath(os.path.expanduser(args.source_dir))
                   if args.source_dir
                   else os.path.join(home, "Public", "external_skills"))
    hermes_home = (os.path.abspath(os.path.expanduser(args.hermes_home))
                   if args.hermes_home
                   else os.path.join(home, ".hermes"))
    src = os.path.join(source_root, args.skill)

    if is_default:
        target = os.path.join(hermes_home, "skills", args.skill)
        mode = "default"
    else:
        target = os.path.join(hermes_home, "profiles", raw_profile, "skills", args.skill)
        mode = f"profile [{raw_profile}]"

    print(f">> 模式: {mode}")
    print(f">> 源:   {src}")
    print(f">> 目标: {target}")

    if not os.path.isdir(src):
        print(f"[FAIL] 源目录不存在: {src}", file=sys.stderr)
        return 1

    sync_py = resolve_sync_dir(args.sync_dir)
    if not os.path.isfile(sync_py):
        print(f"[FAIL] 找不到 sync_dir.py: {sync_py}", file=sys.stderr)
        print("提示：可用 --sync-dir 指定其路径", file=sys.stderr)
        return 1

    sync_cmd = [sys.executable, sync_py, src, target]
    for e in EXCLUDE:
        sync_cmd += ["--exclude", e]

    if args.dry_run:
        print(">> 将执行: " + " ".join(sync_cmd))
        print(">> [dry-run] 未实际执行")
        return 0

    rc = run_cmd(sync_cmd)
    if rc is None or rc != 0:
        print("[FAIL] 同步失败", file=sys.stderr)
        return 1

    print(f"✅ 技能已安装: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())