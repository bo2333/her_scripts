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

返回值:
    0 = 成功
    1 = 失败
"""

import argparse
import os
import shutil
import subprocess
import sys


# 同步时排除的目录名（等价于 rsync --exclude='node_modules' --exclude='.git'）
EXCLUDE_DIRS = {"node_modules", ".git"}


class _ArgumentParser(argparse.ArgumentParser):
    """参数错误时返回码为 1，与脚本语义保持一致。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "copy_install_plugin.py",
        description=(
            "在容器内部署并启用 Hermes 插件。\n"
            "插件源码默认位于 $HOME/Public/external_plugins/<plugin>，\n"
            "将被同步到全局插件目录，或指定 profile 的插件目录。"
        ),
        add_help=False,
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-help", action="help", help="显示此帮助信息并退出")
    parser.add_argument("plugin", metavar="<plugin>",
                        help="插件名称，例如 hermes-lcm")
    parser.add_argument("profile", metavar="[profile]", nargs="?", default=None,
                        help="可选的 Agent Profile 名称；省略时部署到全局插件目录")
    return parser


# ---------------------------------------------------------------------------
# 文件同步
# ---------------------------------------------------------------------------

def sync_with_rsync(src: str, dst: str) -> bool:
    """使用 rsync 做镜像同步（--delete + 排除 node_modules/.git）。"""
    cmd = [
        "rsync", "-av", "--delete",
        "--exclude=node_modules",
        "--exclude=.git",
        f"{src}/", f"{dst}/",
    ]
    try:
        return subprocess.run(cmd).returncode == 0
    except OSError as exc:
        print(f"[WARN] 调用 rsync 失败: {exc}", file=sys.stderr)
        return False


def sync_with_python(src: str, dst: str) -> bool:
    """无 rsync 时的 Python 兜底同步：
    先清空目标（保留排除目录，模拟 rsync --delete --exclude），再复制源内容。
    """
    try:
        # 1. 清空目标内容（但保留 EXCLUDE_DIRS 中的条目）
        for entry in os.listdir(dst):
            if entry in EXCLUDE_DIRS:
                continue
            path = os.path.join(dst, entry)
            if os.path.islink(path) or not os.path.isdir(path):
                os.remove(path)
            else:
                shutil.rmtree(path)

        # 2. 复制源内容（跳过 EXCLUDE_DIRS）
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


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    plugin = args.plugin
    profile = args.profile

    home = os.path.expanduser("~")
    src_path = os.path.join(home, "Public", "external_plugins", plugin)
    hermes_home = os.path.join(home, ".hermes")

    # 1. 前置检查：源目录必须存在
    if not os.path.isdir(src_path):
        print(f"错误: 容器内源目录不存在: {src_path}", file=sys.stderr)
        print("请确保插件代码已复制到该路径 (例如通过 docker cp 或 volume)",
              file=sys.stderr)
        return 1

    # 2. 动态确定目标路径与启用命令
    if profile:
        target_dir = os.path.join(
            hermes_home, "profiles", profile, "plugins", plugin
        )
        enable_cmd = ["hermes", "-p", profile, "plugins", "enable", plugin]
        mode_desc = f"Profile [{profile}]"
    else:
        target_dir = os.path.join(hermes_home, "plugins", plugin)
        enable_cmd = ["hermes", "plugins", "enable", plugin]
        mode_desc = "Global Default"

    print(f">> 模式: {mode_desc}")
    print(f">> 目标目录: {target_dir}")

    # 3. 创建目标目录
    try:
        os.makedirs(target_dir, exist_ok=True)
    except OSError as exc:
        print(f"[FAIL] 创建目标目录失败: {exc}", file=sys.stderr)
        return 1

    # 4. 同步文件
    if shutil.which("rsync"):
        print(">> 使用 rsync 同步文件...")
        ok = sync_with_rsync(src_path, target_dir)
    else:
        print(">> 使用 cp 同步文件...")
        ok = sync_with_python(src_path, target_dir)

    if not ok:
        print("[FAIL] 同步文件失败", file=sys.stderr)
        return 1

    # 5. 启用插件（在目标目录下执行）
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
        print(f"[FAIL] 启用插件失败 (exit {result.returncode})",
              file=sys.stderr)
        return 1

    # 6. 完成
    bar = "=" * 66
    print(bar)
    print("✅ 部署成功！")
    print(f"   位置: {target_dir}")
    if profile:
        print(f"   Profile: {profile} {plugin}")
    print(bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())