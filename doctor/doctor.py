#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes 扩展环境体检。

用法:
    ./doctor.py -help
    ./doctor.py
    ./doctor.py --json
    ./doctor.py --hermes-home /opt/hermes

检查项:
    - hermes 根目录存在且可访问
    - 每个 profile 的 plugins/skills/bin 目录状态
    - 悬空软链接（FAIL）
    - bin 下文件无可执行位（WARN）
    - 安装项对应的源目录不存在（WARN，孤儿）
    - hermes CLI 是否在 PATH（WARN）
    - rsync 是否安装（WARN，影响 copy_install_* 分支）

返回值:
    0 = 无 FAIL
    1 = 存在 FAIL
"""

import argparse
import json
import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, os.pardir, "file"))
import hermes_paths as hp  # noqa: E402


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[ERROR] {message}", file=sys.stderr)
        sys.exit(1)


def build_parser():
    p = _ArgumentParser(
        prog=os.path.basename(sys.argv[0]) or "doctor.py",
        description="Hermes 扩展环境体检（不修改任何文件）。",
        add_help=False, allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("-help", action="help", help="显示帮助并退出")
    p.add_argument("--hermes-home", metavar="<dir>", default=None,
                   help="hermes 根目录（默认 $HOME/.hermes）")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    return p


def _add(checks, level, name, msg):
    checks.append({"level": level, "name": name, "message": msg})


def collect(hh):
    checks = []

    # 1) hermes home
    if os.path.isdir(hh):
        _add(checks, "PASS", "hermes-home", f"{hh} 存在")
    else:
        _add(checks, "FAIL", "hermes-home", f"{hh} 不存在")
        return checks  # 后续检查无意义

    # 2) profiles
    try:
        profiles = hp.list_profiles(hh=hh)
        _add(checks, "PASS", "profiles",
             f"{len(profiles)} 个: {', '.join(n for n, _ in profiles) or '(无)'}")
    except OSError as exc:
        _add(checks, "FAIL", "profiles", f"读取失败: {exc}")
        return checks

    # 3) 每个 profile 的目录结构
    for pname, ppath in profiles:
        for kind in hp.KINDS:
            d = os.path.join(ppath, kind)
            label = f"{pname}/{kind}"
            if os.path.isdir(d):
                continue
            if os.path.exists(d):
                _add(checks, "FAIL", label, f"不是目录: {d}")
            else:
                _add(checks, "WARN", label, f"目录不存在: {d}")

    # 4) 遍历安装项：悬空链接、可执行位、孤儿
    for kind, name, pname, path, _ in hp.iter_installed(hh):
        label = f"{pname}/{kind}/{name}"
        if os.path.islink(path):
            if not os.path.exists(path):
                _add(checks, "FAIL", label, f"悬空软链接 -> {os.readlink(path)}")
            continue
        if kind == "bin" and os.path.isfile(path):
            try:
                if not (os.stat(path).st_mode & 0o111):
                    _add(checks, "WARN", label, "无可执行位")
            except OSError as exc:
                _add(checks, "WARN", label, f"stat 失败: {exc}")
        src = hp.source_of(kind, name)
        if not os.path.lexists(src):
            _add(checks, "WARN", label, f"源不存在: {src}")

    # 5) 依赖
    if shutil.which("hermes"):
        _add(checks, "PASS", "hermes-cli", "在 PATH")
    else:
        _add(checks, "WARN", "hermes-cli", "不在 PATH")
    if shutil.which("rsync"):
        _add(checks, "PASS", "rsync", "已安装")
    else:
        _add(checks, "WARN", "rsync", "未安装（copy_install_* 将用 Python 兜底）")

    return checks


def main(argv=None):
    args = build_parser().parse_args(argv)
    hh = hp.hermes_home(args.hermes_home)
    checks = collect(hh)

    summary = {
        "pass": sum(1 for c in checks if c["level"] == "PASS"),
        "warn": sum(1 for c in checks if c["level"] == "WARN"),
        "fail": sum(1 for c in checks if c["level"] == "FAIL"),
    }

    if args.json:
        print(json.dumps({"checks": checks, "summary": summary},
                         ensure_ascii=False))
    else:
        for c in checks:
            print(f"[{c['level']:<4}] {c['name']:<32} {c['message']}")
        print(f"汇总: PASS={summary['pass']} WARN={summary['warn']} "
              f"FAIL={summary['fail']}")

    return 1 if summary["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())