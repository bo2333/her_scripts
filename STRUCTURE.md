# Hermes Agent 脚本工具箱 — 目录结构与脚本清单

> 本文描述目录布局、脚本清单与常用命令示例。
> **编写规范、Git 流程、检查清单见 [README.md](README.md)。**

---

## 1. 目录结构

### 1.1 公共源目录（`~/Public/`）

脚本从这些目录读取源文件；这些目录通常是 Git 仓库或共享存储。

```text
~/Public/
├── external_bin            # 可执行文件源
├── external_mcp            # MCP 源（本套脚本暂不处理）
├── external_plugins        # 插件源
├── external_skills         # 技能源
└── external_scripts        # 本套脚本的本地主副本（Git 工作树，远端为 GitHub）
```

### 1.2 Hermes 安装目录（`~/.hermes/`）

Default 主 profile 直接位于 `~/.hermes/` 下；命名 profile 位于 `~/.hermes/profiles/<name>/` 下，结构相同。

```text
~/.hermes/                     # default 主 profile 根
├── bin/                       # 可执行文件
├── plugins/                   # 插件
├── skills/                    # 技能
├── scripts/                   # 本套脚本（Git 工作副本，远端为主副本）
└── profiles/
    └── <profile>/             # 命名 profile，结构与 default 相同
        ├── bin/
        ├── plugins/
        ├── skills/
        └── scripts/
```

> **约定**：省略 profile 参数 或 显式传 `default`，均表示操作 default 主 profile。
> **约定**：`~/.hermes/scripts` 是一个 Git 工作副本，包含 `.git/` 目录。

### 1.3 脚本目录树（`~/Public/external_scripts/`）

`~/.hermes/scripts` 与之结构完全相同。

```text
~/Public/external_scripts/    # 本地主副本（git clone 自 GitHub）
├── .git/                     # Git 元数据
│   └── hooks/
│       └── post-receive      # 部署后自动补推 GitHub（由 file/hooks/ 复制而来）
├── file/                     # 通用工具库
│   ├── create_symlink.py     # 创建/更新软链接
│   ├── remove_symlink.py     # 删除软链接
│   ├── sync_dir.py           # 目录镜像同步（rsync-like）
│   ├── sync_push.sh          # 推送当前仓库到主副本，并补推 GitHub
│   ├── hermes_paths.py       # 共享路径库（供 doctor/gc/manifest/batch 使用）
│   └── hooks/
│       └── post-receive      # 主副本 hook 模板（部署时复制到 .git/hooks/）
├── profiles/
│   └── list_profiles.py      # 列出所有 profile
├── plugin/                   # 插件管理
│   ├── symlink_install_plugin.py
│   ├── copy_install_plugin.py
│   ├── clean_plugin.py
│   └── init_plugin.py
├── skills/                   # 技能管理
│   ├── symlink_install_skills.py
│   ├── copy_install_skills.py
│   ├── clean_skills.py
│   └── init_skills.py
├── bin/                      # 可执行文件管理
│   ├── symlink_install_bin.py
│   ├── copy_install_bin.py
│   ├── clean_bin.py
│   └── init_bin.py
├── doctor/                   # 巡检
│   ├── check_deps.py
│   └── doctor.py
└── gc/                       # 垃圾回收
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
| `file/sync_push.sh` | 推送当前仓库到主副本，再由主副本补推 GitHub（失败不阻塞） |
| `file/hermes_paths.py` | 共享路径与 profile 工具库（供 `doctor/`、`gc/`、`manifest/`、`batch/` 使用） |
| `file/hooks/post-receive` | 主副本 hook 模板：收到 push 后自动补推 GitHub |

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

## 3. 快速开始（命令示例）

> 初始化 clone、Git 更新、补推 GitHub 等运维操作见 [README.md 第 3 节](README.md#3-初始化与日常运维)。
> 以下命令在 `~/.hermes/scripts` 目录下执行。

### 3.1 安装插件 / 技能 / 可执行文件

```bash
cd ~/.hermes/scripts

# 插件：软链接方式安装到 default
./plugin/symlink_install_plugin.py hermes-lcm

# 插件：复制方式安装到 profile=ceo
./plugin/copy_install_plugin.py hermes-lcm ceo

# 技能：软链接方式安装到 default
./skills/symlink_install_skills.py my-skill

# 可执行文件：软链接方式安装到 default
./bin/symlink_install_bin.py ripgrep
```

### 3.2 执行安装后的初始化脚本

```bash
# 插件
./plugin/init_plugin.py hermes-lcm ./scripts/install.sh ceo

# 技能
./skills/init_skills.py my-skill ./scripts/install.sh

# 可执行文件（在 ~/.hermes/bin 目录内执行）
./bin/init_bin.py ripgrep ./setup.sh
```

### 3.3 卸载

```bash
# 插件：disable + remove
./plugin/clean_plugin.py hermes-lcm ceo

# 技能：uninstall
./skills/clean_skills.py my-skill ceo

# 可执行文件：直接删除
./bin/clean_bin.py ripgrep ceo
```

### 3.4 巡检与清理

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

### 3.5 列出 profile

```bash
python3 profiles/list_profiles.py
python3 profiles/list_profiles.py --paths
python3 profiles/list_profiles.py --json
```