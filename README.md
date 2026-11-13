# Hermes Agent 脚本工具箱

> 一套以软链接 / 复制两种方式安装、管理、巡检 Hermes Agent 插件、技能、可执行文件的脚本集合。

- 所有脚本支持 `-help` 查看用法。
- 所有脚本参数化，默认值可通过参数覆盖。
- **新增脚本必须按第 5 节「新增脚本规范」同步更新本说明。**
- **分发方式**：`~/Public/external_scripts` 是本地主副本（远端为 GitHub）；各环境 `~/.hermes/scripts` 从主副本 clone / pull，不直接涉及 GitHub。详见 3.1。

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

### 1.3 脚本目录（`~/Public/external_scripts/`，即仓库根）

`~/.hermes/scripts` 与之结构完全相同。

```text
~/Public/external_scripts/    # 本地主副本（git clone 自 GitHub）
├── .git/                     # Git 元数据
├── file/                     # 通用工具库
│   ├── create_symlink.py     # 创建/更新软链接
│   ├── remove_symlink.py     # 删除软链接
│   ├── sync_dir.py           # 目录镜像同步（rsync-like）
│   └── hermes_paths.py       # 共享路径库（供 doctor/gc/manifest/batch 使用）
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

### 3.1 初始化接入（Git clone）

拓扑关系：

```text
GitHub (bo2333/hermes_scripts)
   │  clone / push / fetch（网络允许时）
   ▼
~/Public/external_scripts          # 本地主副本（唯一修改入口）
   │  clone / pull（本地路径，稳定）
   ▼
~/.hermes/scripts                  # 各环境工作副本（只 pull，不直接连 GitHub）
```

- **`~/Public/external_scripts`**：本地主副本，远端为 GitHub。所有代码修改在此提交，再按需推 GitHub。
- **`~/.hermes/scripts`**：各环境独立工作副本，远端是 `~/Public/external_scripts`。**不涉及 GitHub**。

#### 3.1.1 建立本地主副本（一次性）

从 GitHub 获取主副本到 `~/Public/external_scripts`。网络不稳时重试几次即可：

```bash
cd ~/Public
git clone https://github.com/bo2333/hermes_scripts.git external_scripts
```

确认 remote：

```bash
cd ~/Public/external_scripts
git remote -v
# origin  https://github.com/bo2333/hermes_scripts.git (fetch)
# origin  https://github.com/bo2333/hermes_scripts.git (push)
```

#### 3.1.2 每个环境各自 clone

在**每一套** hermes-agent 环境里执行一次：

```bash
# 先清掉旧的 scripts 目录（如有）
rm -rf ~/.hermes/scripts

# 从本地主副本 clone（走本地路径，Git 自动用 hardlink，很快）
git clone ~/Public/external_scripts ~/.hermes/scripts
```

确认 remote：

```bash
cd ~/.hermes/scripts
git remote -v
# origin  /home/<user>/Public/external_scripts (fetch)
# origin  /home/<user>/Public/external_scripts (push)
```

`~/.hermes/scripts` 的 remote 只有本地主副本，**不会出现 GitHub 地址**。脚本内部 `<脚本目录>/../file/` 的相对路径探测仍然有效。

### 3.2 更新 / 合并 / 提交

#### 3.2.1 修改（在主副本）

所有修改在 `~/Public/external_scripts` 中进行：

```bash
cd ~/Public/external_scripts
git pull origin main            # 先从 GitHub 拉最新（网络允许时）
# ... 修改脚本 / README ...
git add -A
git commit -m "feat: xxx"
git push origin main            # 推到 GitHub（网络允许时）
```

#### 3.2.2 各环境同步

各环境从主副本拉取：

```bash
cd ~/.hermes/scripts
git pull origin main
```

`~/.hermes/scripts` 的 `origin` 是本地路径，pull 不依赖网络。

#### 3.2.3 冲突处理

多个环境一般不会冲突（它们只 pull、不 push）。冲突只可能发生在 `~/Public/external_scripts` 从 GitHub pull 时：

```bash
cd ~/Public/external_scripts
git pull origin main
# 若有冲突：
#   edit 冲突文件 → git add <file> → git commit
# 放弃本次 pull：
#   git merge --abort
```

**不要用 `git push -f`**，除非确认要覆盖远端历史。

#### 3.2.4 GitHub 不可用时的处理

`~/Public/external_scripts` 与 `~/.hermes/scripts` 的本地协作**完全不依赖 GitHub**：

- 主副本上的 commit 正常进行，只是暂不 `git push`。
- 各环境从主副本 `git pull` 正常进行。
- 等 GitHub 恢复后，在主副本执行 `git push origin main` 补推即可。

#### 3.2.5 版本隔离（多环境需要不同版本时）

```bash
cd ~/.hermes/scripts
git fetch --tags
git checkout v1.2.0      # 钉在某个标签

# 回到主线
git checkout main
git pull origin main
```

### 3.3 安装插件 / 技能 / 可执行文件

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

### 3.4 执行安装后的初始化脚本

```bash
# 插件
./plugin/init_plugin.py hermes-lcm ./scripts/install.sh ceo

# 技能
./skills/init_skills.py my-skill ./scripts/install.sh

# 可执行文件（在 ~/.hermes/bin 目录内执行）
./bin/init_bin.py ripgrep ./setup.sh
```

### 3.5 卸载

```bash
# 插件：disable + remove
./plugin/clean_plugin.py hermes-lcm ceo

# 技能：uninstall
./skills/clean_skills.py my-skill ceo

# 可执行文件：直接删除
./bin/clean_bin.py ripgrep ceo
```

### 3.6 巡检与清理

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
| **分发拓扑** | `~/Public/external_scripts`（主副本，远端 GitHub）→ `~/.hermes/scripts`（各环境工作副本，远端为主副本） |
| **修改入口** | 只在 `~/Public/external_scripts` 中修改并 commit；各环境只 pull |
| **GitHub 依赖** | 仅主副本的 `git pull/push` 依赖 GitHub；各环境同步走本地路径，不依赖网络 |
| **默认 profile** | 省略 profile 或传 `default`，均操作 `~/.hermes/` 主 profile |
| **源目录** | 默认 `~/Public/external_{plugins,skills,bin}`，可通过 `--source-dir` 覆盖 |
| **Hermes 根** | 默认 `~/.hermes`，可通过 `--hermes-home` 覆盖 |
| **软链接安全** | 删除/替换软链接时只删链接本身，不跟随进入源目录 |
| **dry-run** | 所有会修改文件的脚本支持 `--dry-run` 先演练 |
| **返回码** | `0` = 成功；`1` = 失败或存在需要关注的问题 |
| **共享库** | 路径与 profile 枚举逻辑统一收敛在 `file/hermes_paths.py`，避免重复实现 |
| **禁止 force push** | 不得对 `origin` 执行 `git push -f`，除非确认覆盖远端历史 |

---

## 5. 新增脚本规范

新增脚本时，**代码**必须满足 5.1 的硬性要求，**文档**必须同步更新 5.2 列出的位置，**Git 工作流**按 5.3 执行。三项缺一不可。

### 5.1 脚本必须满足的规范

| # | 规范 | 说明 |
|:---|:---|:---|
| 1 | 支持 `-help` | 用 `add_help=False` + `add_argument("-help", action="help")`；`allow_abbrev=False` |
| 2 | 参数化 | 路径、profile、源根等不得硬编码；默认值可通过参数覆盖 |
| 3 | default 归一 | profile 参数用 `profile is None or profile == "default"` 判断，不得用 `if profile:` |
| 4 | 软链接安全 | 删除/替换目标时先 `os.path.islink` 判断，只删链接本身，不跟随 |
| 5 | dry-run | 会修改文件的脚本提供 `--dry-run`，打印计划后返回 0 |
| 6 | 返回码 | `0` = 成功；`1` = 失败。参数错误也返回 1（自定义 `_ArgumentParser.error`） |
| 7 | 共享库 | 路径计算、profile 枚举优先用 `file/hermes_paths.py`，不要重复实现 |
| 8 | 复用工具 | 建软链接用 `file/create_symlink.py`；目录同步用 `file/sync_dir.py`；不要复制其逻辑 |
| 9 | 不碰源目录 | 任何 clean/卸载脚本只操作目标侧，源目录由 Git 管理 |

### 5.2 文档必须同步更新的位置

新增脚本后，按顺序检查并更新：

| # | 位置 | 更新内容 |
|:---|:---|:---|
| 1 | **1.3 脚本目录** | 在目录树中加上新脚本的路径与一行注释 |
| 2 | **2.x 脚本清单** | 在对应分类的表格中新增一行：`脚本路径` + `说明`；若开新分类，新增一个 `2.x` 小节 |
| 3 | **3.3 ~ 3.6** | 若新脚本有典型用法，在对应小节补一条示例，或新增小节 |
| 4 | **4. 设计约定** | 若新脚本引入了新约定（如新的返回码语义、新的默认路径），在此表补一行 |
| 5 | **5.1 脚本规范** | 若新脚本引入了新的硬性要求（如新增 `--json` 输出约定），在此表补一行 |

例：新增 manifest/generate.py 时，需改 1.3 目录树、2.x 清单（新开 2.8 小节）、3.x 快速开始、4 设计约定（如有）、5.1 脚本规范（如有）。

### 5.3 修改后的 Git 工作流

**所有修改（代码 + README）必须在主副本 `~/Public/external_scripts` 中完成。**

```bash
cd ~/Public/external_scripts

# 1. 改之前先拉取（网络允许时）
git pull origin main

# 2. 修改脚本 + 更新 README（第 5.2 节列出的位置）

# 3. 本地验证
./<新脚本> -help                     # 确认 -help 可用
python3 doctor/check_deps.py         # 依赖齐全
python3 doctor/doctor.py             # 体检无 FAIL

# 4. 提交
git add -A
git commit -m "feat(<scope>): 新增 <脚本名>"   # 或 fix:/docs:/refactor:

# 5. 推 GitHub（网络允许时；不可用则跳过，稍后补推）
git push origin main

# 6. 各环境同步（各环境自行执行）
cd ~/.hermes/scripts && git pull origin main
```

**提交信息约定**（建议，便于 changelog 与审计）：

| 前缀 | 用途 |
|:---|:---|
| `feat:` | 新增脚本或功能 |
| `fix:` | 修复 bug |
| `docs:` | 仅 README / 注释变更 |
| `refactor:` | 重构，不改行为 |
| `chore:` | 构建、依赖、杂项 |

### 5.4 新增脚本检查清单

提交前逐项确认：

```text
[ ] 脚本支持 -help 且输出包含用法、参数说明、返回值
[ ] 所有路径/参数可通过参数覆盖，无硬编码
[ ] profile 判断使用 is None or == "default"
[ ] 会改文件的脚本支持 --dry-run
[ ] 删除目标时先判断 islink，只删链接本身
[ ] 路径/profile 枚举复用 file/hermes_paths.py
[ ] 建链接复用 file/create_symlink.py，目录同步复用 file/sync_dir.py
[ ] 返回码语义为 0 成功 / 1 失败
[ ] README 1.3 目录树已更新
[ ] README 2.x 脚本清单已更新
[ ] README 3.x 快速开始已补示例（如有典型用法）
[ ] README 4 设计约定已补（如引入新约定）
[ ] README 5.1 脚本规范已补（如引入新硬性要求）
[ ] 已在 ~/Public/external_scripts 中 commit
[ ] GitHub 可用时已 push；不可用时已记录待补推
```