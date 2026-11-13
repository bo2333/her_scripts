#!/usr/bin/env bash
# =============================================================================
# 推送到本地主副本，再由主副本补推 GitHub。
#
# 用法:
#   ./sync_push.sh                    # 推送当前目录所在的仓库
#   ./sync_push.sh <repo_dir>         # 推送指定仓库
#   ./sync_push.sh <repo_dir> <branch>
#   ./sync_push.sh --no-github        # 只推主副本，不补推 GitHub
#
# 行为:
#   1) git -C <repo> push origin <branch>     # 失败 → 返回 1
#   2) git -C <main> push origin <branch>     # 失败 → 仅警告，返回 0
#
# 说明:
#   - 主副本路径默认 $HOME/Public/external_scripts，可用 MAIN_REPO 覆盖
#   - 默认分支 main，可用第二个位置参数覆盖
#   - 前提：主副本已配置 receive.denyCurrentBranch=updateInstead
# =============================================================================
set -uo pipefail

MAIN="${MAIN_REPO:-$HOME/Public/external_scripts}"
BRANCH="main"
PUSH_GITHUB=1
REPO=""

usage() {
    sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
    case "$1" in
        -help|--help|-h)
            usage
            exit 0
            ;;
        --no-github)
            PUSH_GITHUB=0
            shift
            ;;
        -*)
            echo "[ERROR] 未知参数: $1" >&2
            usage >&2
            exit 1
            ;;
        *)
            if [ -z "$REPO" ]; then
                REPO="$1"
            else
                BRANCH="$1"
            fi
            shift
            ;;
    esac
done

REPO="${REPO:-$PWD}"

if [ ! -d "$REPO/.git" ]; then
    echo "[FAIL] 不是 Git 仓库: $REPO" >&2
    exit 1
fi

if [ ! -d "$MAIN/.git" ]; then
    echo "[FAIL] 主副本不是 Git 仓库: $MAIN" >&2
    exit 1
fi

# 1) 推送到主副本
echo ">> push $REPO -> origin $BRANCH"
if ! git -C "$REPO" push origin "$BRANCH"; then
    echo "[FAIL] 推送到主副本失败" >&2
    exit 1
fi

# 2) 主副本补推 GitHub（失败不阻塞）
if [ "$PUSH_GITHUB" -eq 1 ]; then
    echo ">> push $MAIN -> origin $BRANCH (GitHub)"
    if ! git -C "$MAIN" push origin "$BRANCH"; then
        echo "[WARN] GitHub 推送失败；本地 commit 已保留，稍后可手动补推:" >&2
        echo "       git -C $MAIN push origin $BRANCH" >&2
    fi
fi

exit 0