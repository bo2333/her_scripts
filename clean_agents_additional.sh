#!/bin/bash

# ==============================================================================
# 脚本名称: clean_agents_additional.sh
# 功能描述: 遍历 hermes-agent 主目录下的子 agent，删除指定路径下的文件或软链接
# 用法示例: 删除：monitor_action_master
#   1. 模拟运行 (推荐): ./clean_agents_additional.sh --base-dir ~/.hermes/profiles --rel-path plugins --target monitor_action_master
#   2. 实际执行:       ./clean_agents_additional.sh --base-dir ~/.hermes/profiles --rel-path plugins --target monitor_action_master --execute
# ==============================================================================

# 默认配置
DRY_RUN=true
BASE_DIR=""
REL_PATH=""
TARGET_NAME=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --base-dir)
            BASE_DIR="$2"
            shift 2
            ;;
        --rel-path)
            REL_PATH="$2"
            shift 2
            ;;
        --target)
            TARGET_NAME="$2"
            shift 2
            ;;
        --execute)
            DRY_RUN=false
            shift
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 参数校验
if [[ -z "$BASE_DIR" || -z "$REL_PATH" || -z "$TARGET_NAME" ]]; then
    echo "错误: 缺少必要参数"
    echo "用法: $0 --base-dir <主目录> --rel-path <相对路径> --target <文件名> [--execute]"
    exit 1
fi

# 验证主目录是否存在
if [[ ! -d "$BASE_DIR" ]]; then
    echo "错误: 主目录不存在 -> $BASE_DIR"
    exit 1
fi

# 标准化相对路径：去除首尾斜杠，防止拼接出错
# 例如: "/logs/" -> "logs", "logs" -> "logs"
CLEAN_REL_PATH=$(echo "$REL_PATH" | sed 's:/*$::' | sed 's:^/*::')

echo "=========================================="
echo " Hermes Agent 清理任务配置"
echo "=========================================="
echo " 主目录:   $BASE_DIR"
echo " 相对路径: $CLEAN_REL_PATH"
echo " 目标名称: $TARGET_NAME"
echo " 模式:     $(if $DRY_RUN; then echo '[模拟运行] 不会实际删除'; else echo '[实际执行] 将永久删除'; fi)"
echo "=========================================="

FOUND_COUNT=0
DELETED_COUNT=0
ERROR_COUNT=0

# 遍历主目录下的所有一级子目录
for SUB_AGENT_DIR in "$BASE_DIR"/*/; do
    # 检查 glob 是否匹配到真实目录 (防止没有子目录时进入循环)
    if [[ ! -d "$SUB_AGENT_DIR" ]]; then
        continue
    fi

    # 获取子目录名称（可选，用于日志）
    SUB_AGENT_NAME=$(basename "$SUB_AGENT_DIR")

    # 拼接完整目标路径
    # 注意: SUB_AGENT_DIR 末尾已有斜杠，CLEAN_REL_PATH 无首尾斜杠
    FULL_PATH="${SUB_AGENT_DIR}${CLEAN_REL_PATH}/${TARGET_NAME}"

    # 检查路径是否存在 (包括失效的软链接)
    # -e: 文件/目录/链接存在
    # -L: 是软链接
    if [[ -e "$FULL_PATH" || -L "$FULL_PATH" ]]; then
        FOUND_COUNT=$((FOUND_COUNT + 1))

        # 判断类型
        if [[ -L "$FULL_PATH" ]]; then
            TYPE_INFO=" (软链接)"
            # 获取软链接指向的目标，用于日志展示（可选）
            LINK_TARGET=$(readlink "$FULL_PATH")
        else
            TYPE_INFO=" (普通文件)"
            LINK_TARGET=""
        fi

        echo "发现: $FULL_PATH $TYPE_INFO"
        if [[ -n "$LINK_TARGET" ]]; then
            echo "  -> 指向: $LINK_TARGET"
        fi

        if $DRY_RUN; then
            echo "  -> [跳过] 模拟模式"
            DELETED_COUNT=$((DELETED_COUNT + 1))
        else
            # 执行删除
            # 重要: 不使用 -r，防止软链接指向目录时递归删除目标内容
            # rm 命令本身即可删除软链接和普通文件
            if rm "$FULL_PATH"; then
                echo "  -> [成功] 已删除"
                DELETED_COUNT=$((DELETED_COUNT + 1))
            else
                echo "  -> [失败] 权限不足或文件被占用"
                ERROR_COUNT=$((ERROR_COUNT + 1))
            fi
        fi
    fi
done

echo "=========================================="
echo " 统计结果:"
echo " 发现目标: $FOUND_COUNT"
echo " 处理成功: $DELETED_COUNT"
echo " 处理失败: $ERROR_COUNT"
echo "=========================================="

if $DRY_RUN && $FOUND_COUNT -gt 0; then
    echo "提示: 当前为模拟模式。若确认路径无误，请添加 --execute 参数重新运行以真正删除。"
fi
