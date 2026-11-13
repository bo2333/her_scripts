#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共享路径与 profile 工具库（供 doctor/gc/manifest/batch 等脚本使用）。

profile 枚举复用 profiles/list_profiles.py 的 list_profiles()，避免重复实现。

用法（在其他脚本中）:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    os.pardir, "file"))
    import hermes_paths as hp
"""

import importlib.util
import os

KINDS = ("plugins", "skills", "bin")
EXTERNAL_KINDS = {
    "plugins": "external_plugins",
    "skills": "external_skills",
    "bin": "external_bin",
}

_LIST_PROFILES_MOD = None


def _list_profiles_mod():
    """动态加载 profiles/list_profiles.py（模块级缓存，只加载一次）。

    用 importlib 而非 sys.path.insert，避免污染 sys.path 或与
    "list_profiles" 这个常见名字冲突。
    """
    global _LIST_PROFILES_MOD
    if _LIST_PROFILES_MOD is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            os.pardir, "profiles", "list_profiles.py")
        spec = importlib.util.spec_from_file_location(
            "_hermes_list_profiles", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _LIST_PROFILES_MOD = mod
    return _LIST_PROFILES_MOD


def hermes_home(override=None):
    if override:
        return os.path.abspath(os.path.expanduser(override))
    return os.path.join(os.path.expanduser("~"), ".hermes")


def external_root(kind, override=None):
    """返回某类对象的源根目录（如 ~/Public/external_plugins）。"""
    if override:
        return os.path.abspath(os.path.expanduser(override))
    return os.path.join(os.path.expanduser("~"), "Public", EXTERNAL_KINDS[kind])


def is_default(profile):
    return profile is None or profile == "default"


def profile_base(profile, hh=None):
    """返回 profile 的根目录（default 即 hermes_home）。"""
    hh = hh or hermes_home()
    if is_default(profile):
        return hh
    return os.path.join(hh, "profiles", profile)


def kind_base(kind, profile, hh=None):
    """返回某 profile 下某类对象的存放目录（plugins/skills/bin 目录本身）。"""
    return os.path.join(profile_base(profile, hh), kind)


def target_dir(kind, name, profile, hh=None):
    """返回某对象在某 profile 下的安装路径。"""
    return os.path.join(kind_base(kind, profile, hh), name)


def list_profiles(hh=None, include_default=True, include_hidden=False):
    """复用 profiles/list_profiles.py 的实现，返回 [(name, path), ...]。"""
    hh = hh or hermes_home()
    return _list_profiles_mod().list_profiles(hh, include_default, include_hidden)


def iter_installed(hh=None):
    """遍历所有已安装项，yield (kind, name, profile, path, is_default)。

    只遍历 plugins/skills/bin 目录下的直接子项，跳过隐藏项。
    """
    hh = hh or hermes_home()
    for pname, _ in list_profiles(hh=hh):
        for kind in KINDS:
            base = kind_base(kind, pname, hh)
            if not os.path.isdir(base):
                continue
            try:
                for entry in os.scandir(base):
                    if entry.name.startswith("."):
                        continue
                    yield kind, entry.name, pname, entry.path, (pname == "default")
            except OSError:
                continue


def source_of(kind, name, source_overrides=None):
    """返回某对象的源路径（默认 ~/Public/external_*）。"""
    if source_overrides and kind in source_overrides:
        return os.path.join(source_overrides[kind], name)
    return os.path.join(external_root(kind), name)