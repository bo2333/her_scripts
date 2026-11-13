# Hermes Agent 脚本工具箱

> 一套以软链接 / 复制两种方式安装、管理、巡检 Hermes Agent 插件、技能、可执行文件的脚本集合。

- 所有脚本支持 `-help` 查看用法。
- 所有脚本参数化，默认值可通过参数覆盖。
- 新增脚本请同步更新下方「脚本清单」。

---

## 1. 目录结构

### 1.1 公共源目录（`~/Public/`）

脚本从这些目录读取源文件；这些目录通常是 Git 仓库或共享存储。

```text
~/Public/
├── external_bin        # 可执行文件源
├── external_mcp        # MCP 源（本套脚本暂不处理）
├── external_plugins    # 插件源
├── external_skills     # 技能源
└── external_scripts    # 本套脚本所在目录
```

### 1.2 Hermes 安装目录（`~/.hermes/`）

Default 主 profile 直接位于 `~/.hermes/` 下；命名 profile 位于 `~/.hermes/profiles/<name>/` 下，结构相同。

```text
~/.hermes/                     # default 主 profile 根
├── bin/                       # 可执行文件
├── plugins/                   # 插件
├── skills/                    # 技能
├── scripts/                   # 脚本（本套脚本的部署位置）
└── profiles/
    └── <profile>/             # 命名 profile，结构与 default 相同
        ├── bin/
        ├── plugins/
        ├── skills/
        └── scripts/
```

> **约定**：省略 profile 参数 或 显式传 `default`，均表示操作 default 主 profile。

### 1.3 脚本目录（`~/Public/external_scripts/`）

```text
~/Public/external_scripts/
├── file/                       # 通用工具库
│   ├── create_symlink.py       # 创建/更新软链接
│   ├── remove_symlink.py       # 删除软链接
│   ├── sync_dir.py             # 目录镜像同步（rsync-like）
│   └── hermes_paths.py         # 共享路径库（供 doctor/gc/manifest/batch 使用）
├── profiles/
│   └── list_profiles.py        # 列出所有 profile
├── plugin/                     # 插件管理
│   ├── symlink_install_plugin.py
│   ├── copy_install_plugin.py
│   ├── clean_plugin.py
│   └── init_plugin.py
├── skills/                     # 技能管理
│   ├── symlink_install_skills.py
│   ├── copy_install_skills.py
│   ├── clean_skills.py
│   └── init_skills.py
├── bin/                        # 可执行文件管理
│   ├── symlink_install_bin.py
│   ├── copy_install_bin.py
│   ├── clean_bin.py
│   └── init_bin.py
├── doctor/                     # 巡检
│   ├── check_deps.py
│   └── doctor.py
└── gc/                         # 垃圾回收
    ├── scan.py
    └── clean.py
```

---

## 2. 脚本清单

### 2.1 通用工具（`file/`）

| 脚本 | 说明 |
|:---|:---|
| `file/create_symlink.py` | 创建或更新软链接（源可为文件或目录） |
| `file/remove_symlink.py` | 判断指定位置是否为软链接，是则删除 |
| `file/sync_dir.py` | 目录镜像同步（复制 + 排除 + 处理目标形态），`copy_install_*` 共用 |
| `file/hermes_paths.py` | 共享路径与 profile 工具库（供 `doctor/`、`gc/`、`manifest/`、`batch/` 使用） |

### 2.2 Profile 列表（`profiles/`）

| 脚本 | 说明 |
|:---|:---|
| `profiles/list_profiles.py` | 列出所有 profile（含 default 主 profile），用于批量处理 |

### 2.3 插件管理（`plugin/`）

| 脚本 | 说明 |
|:---|:---|
| `plugin/symlink_install_plugin.py` | **方式 1**：软链接方式导入插件 |
| `plugin/copy_install_plugin.py` | **方式 2**：复制方式导入插件（不能直接软链接时使用） |
| `plugin/clean_plugin.py` | 删除（禁用并移除）插件 |
| `plugin/init_plugin.py` | 执行插件的额外初始化脚本 |

### 2.4 技能管理（`skills/`）

| 脚本 | 说明 |
|:---|:---|
| `skills/symlink_install_skills.py` | **方式 1**：软链接方式导入技能 |
| `skills/copy_install_skills.py` | **方式 2**：复制方式导入技能（不能直接软链接时使用） |
| `skills/clean_skills.py` | 卸载技能 |
| `skills/init_skills.py` | 执行技能的额外初始化脚本 |

### 2.5 可执行文件管理（`bin/`）

| 脚本 | 说明 |
|:---|:---|
| `bin/symlink_install_bin.py` | **方式 1**：软链接方式安装（源可为文件或目录） |
| `bin/copy_install_bin.py` | **方式 2**：复制方式安装（保留可执行位与符号链接） |
| `bin/clean_bin.py` | 卸载（直接删除，不触碰源目录） |
| `bin/init_bin.py` | 在 bin 目录执行安装后初始化脚本 |

### 2.6 巡检（`doctor/`）

| 脚本 | 说明 |
|:---|:---|
| `doctor/check_deps.py` | 检查 Python / hermes CLI / rsync / git 依赖 |
| `doctor/doctor.py` | 扩展环境体检：悬空链接、孤儿、可执行位、目录结构 |

### 2.7 垃圾回收（`gc/`）

| 脚本 | 说明 |
|:---|:---|
| `gc/scan.py` | 扫描垃圾项（悬空链接 / 孤儿 / 结构异常），只读 |
| `gc/clean.py` | 清理悬空链接与孤儿（只删目标侧，`invalid` 仅报告） |

---

## 3. 快速开始

### 3.1 初始化接入

建立好 Hermes Agent 后，手动将本套脚本接入 `~/.hermes/scripts`：

```bash
~/.hermes/tools/python-3.14.9+20261021-linux-x64/bin/python3.14 \
  ./file/create_symlink.py \
  ~/Public/external_scripts \
  ~/.hermes/scripts
```

> 若 `python3` 已在 `PATH` 中，可直接用 `python3 file/create_symlink.py ...`。

### 3.2 安装插件 / 技能 / 可执行文件

```bash
cd ~/Public/external_scripts

# 插件：软链接方式安装到 default
./plugin/symlink_install_plugin.py hermes-lcm

# 插件：复制方式安装到 profile=ceo
./plugin/copy_install_plugin.py hermes-lcm ceo

# 技能：软链接方式安装到 default
./skills/symlink_install_skills.py my-skill

# 可执行文件：软链接方式安装到 default
./bin/symlink_install_bin.py ripgrep
```

### 3.3 执行安装后的初始化脚本

```bash
# 插件
./plugin/init_plugin.py hermes-lcm ./scripts/install.sh ceo

# 技能
./skills/init_skills.py my-skill ./scripts/install.sh

# 可执行文件（在 ~/.hermes/bin 目录内执行）
./bin/init_bin.py ripgrep ./setup.sh
```

### 3.4 卸载

```bash
# 插件：disable + remove
./plugin/clean_plugin.py hermes-lcm ceo

# 技能：uninstall
./skills/clean_skills.py my-skill ceo

# 可执行文件：直接删除
./bin/clean_bin.py ripgrep ceo
```

### 3.5 巡检与清理

```bash
# 依赖检查
python3 doctor/check_deps.py

# 环境体检
python3 doctor/doctor.py
python3 doctor/doctor.py --json | jq '.summary'

# 扫描垃圾
python3 gc/scan.py
python3 gc/scan.py --category broken

# 清理（先演练，再执行）
python3 gc/clean.py --all --dry-run
python3 gc/clean.py --all
```

---

## 4. 设计约定

| 约定 | 说明 |
|:---|:---|
| **默认 profile** | 省略 profile 或传 `default`，均操作 `~/.hermes/` 主 profile |
| **源目录** | 默认 `~/Public/external_{plugins,skills,bin}`，可通过 `--source-dir` 覆盖 |
| **Hermes 根** | 默认 `~/.hermes`，可通过 `--hermes-home` 覆盖 |
| **软链接安全** | 删除/替换软链接时只删链接本身，不跟随进入源目录 |
| **dry-run** | 所有会修改文件的脚本支持 `--dry-run` 先演练 |
| **返回码** | `0` = 成功；`1` = 失败或存在需要关注的问题 |
| **共享库** | 路径与 profile 枚举逻辑统一收敛在 `file/hermes_paths.py`，避免重复实现 |