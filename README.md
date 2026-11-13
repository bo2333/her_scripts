# Hermes Agent 脚本工具箱 — 工作要求

> 本文规定脚本的编写规范、Git 分发与合并流程、自动化运维要求。
> **目录结构、脚本清单、用法示例见 [STRUCTURE.md](STRUCTURE.md)。**
>
> 新增脚本时：本文通常**不需要改**；需要改的是 `STRUCTURE.md`（见第 5 节）。

---

## 1. 文件导航

| 文件 | 内容 | 新增脚本时 |
|:---|:---|:---|
| `README.md`（本文） | 编写规范、Git 流程、自动化要求、设计约定、检查清单 | 通常不改 |
| `STRUCTURE.md` | 目录树、脚本清单、安装/卸载/巡检示例 | **必须更新**（见 5.2） |

---

## 2. Git 拓扑与分发模型

```text
GitHub (bo2333/hermes_scripts.git)
   │  SSH 认证，clone / pull / push（网络允许时）
   ▼
~/Public/external_scripts          # 本地主副本（唯一修改入口）
   │  clone / pull（本地路径，稳定，无认证）
   ▼
~/.hermes/scripts                  # 各环境工作副本（只 pull，不直接连 GitHub）
```

| 角色 | 路径 | 认证方式 | 说明 |
|:---|:---|:---|:---|
| **主副本** | `~/Public/external_scripts` | SSH 密钥 | 本地权威源；远端为 GitHub。所有修改在此提交 |
| **环境工作副本** | `~/.hermes/scripts` | 无（本地路径） | 各 Hermes 环境独立 clone；远端是主副本 |
| **远程备份** | `git@github.com:bo2333/hermes_scripts.git` | SSH 密钥 | 仅主副本与之交互 |

**核心约束**：

- 修改只在主副本 `~/Public/external_scripts` 中进行。
- 各环境默认只 `git pull`，不直接改。
- GitHub 不可用时，本地协作不受影响；commit 保留在主副本，网络恢复后补推。
- **禁止使用 HTTPS 协议访问 GitHub**（GitHub 已停止支持密码认证；交互式 PAT 不适用于自动化）。统一使用 SSH。

---

## 3. 初始化与日常运维

### 3.1 配置 SSH 密钥（一次性，全机器共享）

自动化环境要求**无密码短语（passphrase）的 SSH 密钥**，否则每次 push/pull 都会交互式提示。

```bash
# 1. 确保 ~/.ssh 存在且权限正确
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 2. 若已有密钥，先备份（避免 ssh-keygen 交互式追问覆盖）
[ -f ~/.ssh/id_ed25519 ] && mv ~/.ssh/id_ed25519 ~/.ssh/id_ed25519.bak.$(date +%s)
[ -f ~/.ssh/id_ed25519.pub ] && mv ~/.ssh/id_ed25519.pub ~/.ssh/id_ed25519.pub.bak.$(date +%s)

# 3. 生成无密码短语的密钥（-N "" 是关键）
ssh-keygen -t ed25519 -C "root@$(hostname)" -f ~/.ssh/id_ed25519 -N "" -q

# 4. 权限收紧
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

# 5. 打印公钥，复制到 GitHub → Settings → SSH and GPG keys → New SSH key
cat ~/.ssh/id_ed25519.pub
```

验证：

```bash
ssh -T git@github.com
# 期望：Hi bo2333! You've successfully authenticated...
# 注意：退出码为 1 是 GitHub 的设计，不代表失败
```

### 3.2 预置 GitHub host key（一次性）

防止首次连接时弹出 `Are you sure you want to continue connecting?` 导致自动化挂起：

```bash
ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null
chmod 644 ~/.ssh/known_hosts
```

### 3.3 建立主副本（一次性）

```bash
cd ~/Public
git clone git@github.com:bo2333/hermes_scripts.git external_scripts
```

确认 remote 使用 SSH：

```bash
cd ~/Public/external_scripts
git remote -v
# origin  git@github.com:bo2333/hermes_scripts.git (fetch)
# origin  git@github.com:bo2333/hermes_scripts.git (push)
```

若之前误用 HTTPS，切换：

```bash
cd ~/Public/external_scripts
git remote set-url origin git@github.com:bo2333/hermes_scripts.git
```

### 3.4 允许主副本接收 push（一次性）

主副本是普通仓库（有工作树），必须允许各环境向它 push 并自动更新工作树：

```bash
cd ~/Public/external_scripts
git config receive.denyCurrentBranch updateInstead
```

未配置时，`~/.hermes/scripts` 的 `git push` 会被拒绝：
`! [remote rejected] main -> main (branch is currently checked out)`。

### 3.5 配置拉取策略与自动化编辑器（一次性，主副本 + 各环境）

自动化场景下，`git pull` 遇到冲突会进入交互式 merge 并挂起，`git merge` / `git rebase` 会打开编辑器。统一配置：

```bash
# 主副本
cd ~/Public/external_scripts
git config pull.ff only        # 只允许 fast-forward，冲突直接失败退出
git config core.editor true    # 禁止打开编辑器，接受默认提交信息
git config core.pager cat      # 禁止分页器，日志更干净

# 各环境（每环境执行一次）
cd ~/.hermes/scripts
git config pull.ff only
git config core.editor true
git config core.pager cat
```

### 3.6 部署 post-receive hook（一次性，可选但推荐）

主副本收到 push 后自动补推 GitHub；失败只警告，不阻塞接收。

```bash
cd ~/Public/external_scripts
mkdir -p .git/hooks
cp file/hooks/post-receive .git/hooks/post-receive
chmod +x .git/hooks/post-receive
chmod +x file/sync_push.sh
```

hook 内部已设置 `GIT_TERMINAL_PROMPT=0`，任何认证/交互提示都会直接失败而非挂起。**前提是 3.1、3.2 已完成**，否则 hook 每次都会失败（但不会阻塞主副本接收）。

### 3.7 各环境 clone（每环境一次）

```bash
rm -rf ~/.hermes/scripts
git clone ~/Public/external_scripts ~/.hermes/scripts
```

确认 remote：

```bash
cd ~/.hermes/scripts
git remote -v
# origin  /home/<user>/Public/external_scripts (fetch)
# origin  /home/<user>/Public/external_scripts (push)
```

`~/.hermes/scripts` 的 remote 只有本地主副本，**不会出现 GitHub 地址**，也不涉及 SSH 认证。

### 3.8 日常更新

主副本拉 GitHub → 各环境拉主副本：

```bash
# 主副本
cd ~/Public/external_scripts
git pull --ff-only origin main

# 各环境
cd ~/.hermes/scripts
git pull --ff-only origin main
```

`--ff-only` 显式写在命令里，确保脚本中不依赖全局配置也能正确失败退出。

### 3.9 补推 GitHub

三种方式，任选其一：

| 方式 | 命令 | 适用 |
|:---|:---|:---|
| 主副本直接推 | `cd ~/Public/external_scripts && git push origin main` | 在主副本操作时 |
| `sync_push.sh` | `file/sync_push.sh [<repo>] [<branch>] [--no-github]` | 在环境里改完推回主副本并补推 |
| `post-receive` hook | 部署后自动触发 | 任何来源 push 到主副本时 |

补推失败**不丢任何东西**：commit 已在主副本中，下次 `git push origin main` 会一并带上。

### 3.10 冲突处理

多个环境一般不会冲突（只 pull、不 push）。冲突只可能发生在主副本从 GitHub pull 时：

```bash
cd ~/Public/external_scripts
git pull --ff-only origin main
# 若失败（非 fast-forward）：说明本地和远端都有新提交
#   手动 merge：
#     git pull --no-ff origin main
#     edit 冲突文件 → git add <file> → git commit
#   放弃：
#     git merge --abort
```

**禁止 `git push -f`**，除非确认要覆盖远端历史。

---

## 4. 设计约定

| 约定 | 说明 |
|:---|:---|
| **分发拓扑** | 主副本（远端 GitHub）→ 各环境工作副本（远端为主副本），见第 2 节 |
| **认证方式** | 统一使用 SSH 密钥（无 passphrase）；禁止 HTTPS + 密码 / 交互式 PAT |
| **自动化静默** | hook 与自动化脚本必须设置 `GIT_TERMINAL_PROMPT=0`，任何交互提示应失败而非挂起 |
| **拉取策略** | 脚本中的 pull 必须带 `--ff-only`；全局配置 `pull.ff only` + `core.editor true` |
| **修改入口** | 只在 `~/Public/external_scripts` 中修改并 commit；各环境默认只 pull |
| **GitHub 依赖** | 仅主副本的 pull/push 依赖 GitHub；各环境同步走本地路径 |
| **补推机制** | `sync_push.sh` 或 `post-receive` hook；失败不阻塞，commit 保留 |
| **默认 profile** | 省略 profile 或传 `default`，均操作 `~/.hermes/` 主 profile |
| **源目录** | 默认 `~/Public/external_{plugins,skills,bin}`，可通过 `--source-dir` 覆盖 |
| **Hermes 根** | 默认 `~/.hermes`，可通过 `--hermes-home` 覆盖 |
| **软链接安全** | 删除/替换软链接时只删链接本身，不跟随进入源目录 |
| **dry-run** | 所有会修改文件的脚本支持 `--dry-run` 先演练 |
| **返回码** | `0` = 成功；`1` = 失败或存在需要关注的问题 |
| **共享库** | 路径与 profile 枚举逻辑统一收敛在 `file/hermes_paths.py` |
| **禁止 force push** | 不得对 `origin` 执行 `git push -f`，除非确认覆盖远端历史 |

---

## 5. 新增脚本规范

### 5.1 脚本必须满足的规范

| # | 规范 | 说明 |
|:---|:---|:---|
| 1 | 支持 `-help` | `add_help=False` + `add_argument("-help", action="help")`；`allow_abbrev=False` |
| 2 | 参数化 | 路径、profile、源根等不得硬编码；默认值可通过参数覆盖 |
| 3 | default 归一 | profile 用 `profile is None or profile == "default"` 判断，不得用 `if profile:` |
| 4 | 软链接安全 | 删除/替换目标时先 `os.path.islink` 判断，只删链接本身，不跟随 |
| 5 | dry-run | 会修改文件的脚本提供 `--dry-run`，打印计划后返回 0 |
| 6 | 返回码 | `0` = 成功；`1` = 失败。参数错误也返回 1（自定义 `_ArgumentParser.error`） |
| 7 | 共享库 | 路径计算、profile 枚举优先用 `file/hermes_paths.py` |
| 8 | 复用工具 | 建软链接用 `file/create_symlink.py`；目录同步用 `file/sync_dir.py`；不复制其逻辑 |
| 9 | 不碰源目录 | 任何 clean/卸载脚本只操作目标侧，源目录由 Git 管理 |
| 10 | 自动化静默 | 涉及 Git 操作的脚本必须设置 `GIT_TERMINAL_PROMPT=0`，pull 带 `--ff-only` |

### 5.2 文档必须同步更新的位置（全部在 `STRUCTURE.md`）

新增脚本后，按下表更新 `STRUCTURE.md`。**本文 `README.md` 通常不需要改。**

| # | STRUCTURE.md 中的位置 | 更新内容 |
|:---|:---|:---|
| 1 | **1.3 脚本目录树** | 加上新脚本的路径与一行注释 |
| 2 | **2.x 脚本清单** | 对应分类表格新增一行（路径 + 说明）；开新分类则新增 `2.x` 小节 |
| 3 | **3.x 用法示例** | 若有典型用法，在对应小节补示例，或新增小节 |
| 4 | **附录：设计约定** | 若引入新约定（如新返回码语义、新默认路径），在 STRUCTURE.md 的约定表补一行，并视情况同步本文第 4 节 |

> 判断标准：**描述"有什么"的 → STRUCTURE.md；规定"必须怎么做"的 → 本文**。

### 5.3 修改后的 Git 工作流

所有修改（代码 + 文档）在主副本完成：

```bash
cd ~/Public/external_scripts

# 1. 改之前先拉取
git pull --ff-only origin main

# 2. 修改脚本 + 更新 STRUCTURE.md（5.2 列出的位置）

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
cd ~/.hermes/scripts && git pull --ff-only origin main
```

### 5.4 提交信息约定

| 前缀 | 用途 |
|:---|:---|
| `feat:` | 新增脚本或功能 |
| `fix:` | 修复 bug |
| `docs:` | 仅文档 / 注释变更 |
| `refactor:` | 重构，不改行为 |
| `chore:` | 构建、依赖、杂项 |

### 5.5 新增脚本检查清单

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
[ ] 若涉及 Git 操作：设置 GIT_TERMINAL_PROMPT=0，pull 带 --ff-only
[ ] STRUCTURE.md 1.3 目录树已更新
[ ] STRUCTURE.md 2.x 脚本清单已更新
[ ] STRUCTURE.md 3.x 用法示例已补（如有典型用法）
[ ] STRUCTURE.md 附录设计约定已补（如引入新约定）
[ ] 已在 ~/Public/external_scripts 中 commit
[ ] GitHub 可用时已 push；不可用时已记录待补推
```

---

## 6. 排障速查

| 症状 | 原因 | 处理 |
|:---|:---|:---|
| `Password authentication is not supported` | remote 用了 HTTPS | `git remote set-url origin git@github.com:...` |
| `Author identity unknown` | 未配置 `user.name` / `user.email` | `git config --global user.name/user.email` |
| `Permission denied (publickey)` | SSH 公钥未添加到 GitHub，或私钥权限过宽 | `chmod 600 ~/.ssh/id_ed25519`；确认 GitHub 上有对应公钥 |
| `Host key verification failed` | `known_hosts` 未预置 | 见 3.2 |
| `! [remote rejected] ... branch is currently checked out` | 主副本未配 `receive.denyCurrentBranch` | 见 3.4 |
| `git pull` 挂起无输出 | 冲突进入交互式 merge | 用 `--ff-only` 或 `pull.ff only` |
| `git merge` 打开 vim 卡住 | 未配 `core.editor` | `git config core.editor true` |
| hook 中 push 挂起 | 首次连接 host key 确认 | 见 3.2；hook 已设 `GIT_TERMINAL_PROMPT=0` 会直接失败而非挂起 |