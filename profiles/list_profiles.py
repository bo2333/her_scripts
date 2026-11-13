#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出所有 profile 名字（含 default 主 profile）。

路径约定:
    default 主 profile : ~/.hermes                （目录存在即视为存在）
    其它 profile       : ~/.hermes/profiles/<name>

用法:
    ./list_profiles.py -help
    ./list_profiles.py
    ./list_profiles.py --paths
    ./list_profiles.py --json
    ./list_profiles.py --count
    ./list_profiles.py --no-default

返回值:
    0 = 成功（含目录不存在、结果为空）
    1 = 失败（根目录存在但不是目录、读取失败等）
"""

import argparse
import json
import os
import sys


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def default_hermes_home() -> str:
    return os.path.join(os.path.expanduser("~"), ".hermes")


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "list_profiles.py",
        description=(
            "列出所有 profile 名字（含 default 主 profile）。\n"
            "  default 主 profile : $HOME/.hermes（目录存在即视为存在）\n"
            "  其它 profile       : $HOME/.hermes/profiles/<name>\n"
            "默认每行输出一个名字（按字母序），忽略隐藏项与非目录项；\n"
            "软链接指向目录也算作 profile。"
        ),
        add_help=False,
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根目录（默认 $HOME/.hermes）；default profile 即此目录")
    parser.add_argument("--no-default", action="store_true",
                        help="不输出 default 主 profile")
    parser.add_argument("--paths", action="store_true",
                        help="同时输出每个 profile 的路径（格式：name<TAB>path）")
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 形式输出（--paths 时输出 name->path 映射）")
    parser.add_argument("--count", action="store_true",
                        help="仅输出 profile 数量")
    parser.add_argument("--include-hidden", action="store_true",
                        help="包含 profiles 下以 . 开头的隐藏目录")
    return parser


def list_profiles(hermes_home: str, include_default: bool,
                  include_hidden: bool) -> list:
    """返回 [(name, path), ...]，按 name 字典序排序。"""
    entries = []

    # 1) default 主 profile = hermes_home 本身
    if include_default and os.path.isdir(hermes_home):
        entries.append(("default", hermes_home))

    # 2) profiles 目录下的子目录
    profiles_dir = os.path.join(hermes_home, "profiles")
    if os.path.isdir(profiles_dir):
        with os.scandir(profiles_dir) as it:
            for entry in it:
                if not include_hidden and entry.name.startswith("."):
                    continue
                # 避免与 default 重名（profiles/default 视为普通 profile 会冲突，
                # 这里直接跳过，以 ~/.hermes 为 default 主 profile 的唯一来源）
                if entry.name == "default":
                    continue
                try:
                    if entry.is_dir(follow_symlinks=True):
                        entries.append((entry.name, entry.path))
                except OSError:
                    continue

    entries.sort(key=lambda x: x[0])
    return entries


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    hermes_home = args.hermes_home or default_hermes_home()
    hermes_home = os.path.abspath(os.path.expanduser(hermes_home))

    # 根目录存在但不是目录 → 报错
    if os.path.exists(hermes_home) and not os.path.isdir(hermes_home):
        print(f"[FAIL] hermes 根路径存在但不是目录: {hermes_home}",
              file=sys.stderr)
        return 1

    if not os.path.exists(hermes_home):
        print(f"[WARN] hermes 根目录不存在: {hermes_home}", file=sys.stderr)

    try:
        entries = list_profiles(
            hermes_home,
            include_default=not args.no_default,
            include_hidden=args.include_hidden,
        )
    except OSError as exc:
        print(f"[FAIL] 读取 profiles 目录失败: {exc}", file=sys.stderr)
        return 1

    # 输出
    if args.count:
        print(len(entries))
    elif args.json:
        if args.paths:
            print(json.dumps(dict(entries), ensure_ascii=False))
        else:
            print(json.dumps([n for n, _ in entries], ensure_ascii=False))
    else:
        for name, path in entries:
            if args.paths:
                print(f"{name}\t{path}")
            else:
                print(name)

    return 0


if __name__ == "__main__":
    sys.exit(main())