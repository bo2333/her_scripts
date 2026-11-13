#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件安装方式2，需要移动插件内容

用法:
    ./copy_install_plugin.py -help
    ./copy_install_plugin.py <plugin> [profile]

示例:
    ./copy_install_plugin.py hermes-lcm           # 默认主 default
    ./copy_install_plugin.py hermes-lcm ceo       # 部署到 profile=ceo
    ./copy_install_plugin.py hermes-lcm default   # 显式指定 default（等价于省略）

路径约定:
    default 主 profile : $HOME/.hermes/plugins/<plugin>
    其它 profile       : $HOME/.hermes/profiles/<name>/plugins/<plugin>

安全:
    - 目标本身是软链接（例如之前用 symlink_install_plugin.py 安装过）时，
      先移除链接本身（不跟随链接），再复制，绝不会删除源目录内容。
    - 目标是实体文件/目录时先删除再复制。

返回值:
    0 = 成功
    1 = 失败
"""

import argparse
import os
import shutil
import subprocess
import sys


# 排除目录名（按 basename 匹配任意层级，等价 rsync --exclude='node_modules'）
EXCLUDE_DIRS = {"node_modules", ".git"}


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "copy_install_plugin.py",
        description=(
            "复制安装 hermes-agent 插件。\n"
            "支持 default 主 profile（$HOME/.hermes）与\n"
            "指定 profile（$HOME/.hermes/profiles/<name>）。\n"
            "目标为软链接时会先移除链接本身，避免误删源目录。"
        ),
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("plugin", metavar="<plugin>", help="插件名称，例如 hermes-lcm")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="Profile 名称；省略或传 default 表示主 default profile")
    parser.add_argument("--source-dir", metavar="<dir>", default=None,
                        help="源目录根（默认 $HOME/Public/external_plugins）")
    parser.add_argument("--hermes-home", metavar="<dir>", default=None,
                        help="hermes 根目录（默认 $HOME/.hermes）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划")
    return parser


def sync_with_rsync(src: str, dst: str) -> bool:
    cmd = ["rsync", "-av", "--delete",
           "--exclude=node_modules", "--exclude=.git",
           f"{src}/", f"{dst}/"]
    print(">> " + " ".join(cmd))
    try:
        return subprocess.run(cmd).returncode == 0
    except OSError as exc:
        print(f"[WARN] 调用 rsync 失败: {exc}", file=sys.stderr)
        return False


def _clean_dir(dst: str) -> None:
    """递归清空 dst 内容，但保留任意层级名为 EXCLUDE_DIRS 的目录。

    只删除条目本身；软链接只删链接本身，不跟随。
    """
    for entry in os.listdir(dst):
        if entry in EXCLUDE_DIRS:
            continue
        path = os.path.join(dst, entry)
        if os.path.islink(path) or not os.path.isdir(path):
            os.remove(path)
        else:
            shutil.rmtree(path)


def sync_with_python(src: str, dst: str) -> bool:
    try:
        _clean_dir(dst)
        ignore = shutil.ignore_patterns(*EXCLUDE_DIRS)
        for entry in os.listdir(src):
            if entry in EXCLUDE_DIRS:
                continue
            s = os.path.join(src, entry)
            d = os.path.join(dst, entry)
            if os.path.isdir(s) and not os.path.islink(s):
                shutil.copytree(s, d, ignore=ignore, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d, follow_symlinks=False)
        return True
    except Exception as exc:
        print(f"[FAIL] 同步文件失败: {exc}", file=sys.stderr)
        return False


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    plugin = args.plugin
    raw_profile = args.profile
    # 修复 P1：default 字面值等同省略
    is_default = raw_profile is None or raw_profile == "default"

    home = os.path.expanduser("~")
    source_root = (os.path.abspath(os.path.expanduser(args.source_dir))
                   if args.source_dir
                   else os.path.join(home, "Public", "external_plugins"))
    hermes_home = (os.path.abspath(os.path.expanduser(args.hermes_home))
                   if args.hermes_home
                   else os.path.join(home, ".hermes"))
    src_path = os.path.join(source_root, plugin)

    if is_default:
        target_dir = os.path.join(hermes_home, "plugins", plugin)
        enable_cmd = ["hermes", "plugins", "enable", plugin]
        mode_desc = "Global Default"
    else:
        target_dir = os.path.join(hermes_home, "profiles", raw_profile, "plugins", plugin)
        enable_cmd = ["hermes", "-p", raw_profile, "plugins", "enable", plugin]
        mode_desc = f"Profile [{raw_profile}]"

    print(f">> 模式: {mode_desc}")
    print(f">> 源目录: {src_path}")
    print(f">> 目标目录: {target_dir}")

    if not os.path.isdir(src_path):
        print(f"[FAIL] 源目录不存在: {src_path}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(">> [dry-run] 将：移除目标软链接（如有）→ 清空目标（保留 node_modules/.git）"
              "→ 复制源 → 启用插件")
        return 0

    # 修复 P0：目标本身是软链接时先移除链接本身，避免 sync 跟随进入源目录
    if os.path.islink(target_dir):
        print(f"[INFO] 目标是软链接，移除链接本身（不触碰其指向）: {target_dir}")
        try:
            os.remove(target_dir)
        except OSError as exc:
            print(f"[FAIL] 移除旧软链接失败: {exc}", file=sys.stderr)
            return 1
    elif os.path.exists(target_dir) and not os.path.isdir(target_dir):
        print(f"[WARN] 目标是普通文件，删除: {target_dir}")
        try:
            os.remove(target_dir)
        except OSError as exc:
            print(f"[FAIL] 删除目标文件失败: {exc}", file=sys.stderr)
            return 1

    try:
        os.makedirs(target_dir, exist_ok=True)
    except OSError as exc:
        print(f"[FAIL] 创建目标目录失败: {exc}", file=sys.stderr)
        return 1

    if shutil.which("rsync"):
        print(">> 使用 rsync 同步文件...")
        ok = sync_with_rsync(src_path, target_dir)
    else:
        print(">> 使用 cp 同步文件...")
        ok = sync_with_python(src_path, target_dir)

    if not ok:
        print("[FAIL] 同步文件失败", file=sys.stderr)
        return 1

    print(">> 启用插件...")
    print(f">> 执行命令: {' '.join(enable_cmd)}")
    try:
        result = subprocess.run(enable_cmd, cwd=target_dir)
    except FileNotFoundError:
        print(f"[FAIL] 命令不存在: {enable_cmd[0]}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"[FAIL] 执行启用命令失败: {exc}", file=sys.stderr)
        return 1

    if result.returncode != 0:
        print(f"[FAIL] 启用插件失败 (exit {result.returncode})", file=sys.stderr)
        return 1

    bar = "=" * 66
    print(bar)
    print("✅ 部署成功！")
    print(f"   位置: {target_dir}")
    print(f"   Profile: {'default' if is_default else raw_profile}")
    print(bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())