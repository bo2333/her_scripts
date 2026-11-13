#!/bin/bash

# ==============================================================================
# 此脚本必须在容器内部执行！
# copy_install_plugin.sh <plugin> <profiles>
# copy_install_plugin.sh hermes-lcm  默认 default
# copy_install_plugin.sh hermes-lcm ceo
# ==============================================================================

set -e

if [ $# -lt 1 ]; then
    echo "错误: 缺少必要参数" >&2
    echo "用法: $0 <plugin>" >&2
    echo "示例: $0 copy_install_plugin.sh hermes-lcm" >&2
    exit 1
fi

# ----------------------
# 1. 配置区域 (请根据实际情况修改)
# ----------------------
# 获取传入的参数 (如果在容器内执行脚本时传参)
# 用法: ./deploy_inside_container.sh [agent_name]
HER_PLUGIN="$1"
AGENT_NAME="${2:-}"


# 源路径：容器内插件源码的位置
# 假设你已经通过 docker cp 或 volume 把代码放到了这里
SRC_PATH="$HOME/Public/external_plugins/$HER_PLUGIN" 

# 获取当前用户主目录下的 .hermes 路径
HERMES_HOME="$HOME/.hermes"



# ----------------------
# 2. 前置检查
# ----------------------

if [ ! -d "$SRC_PATH" ]; then
    echo "错误: 容器内源目录不存在: $SRC_PATH"
    echo "请确保插件代码已复制到该路径 (例如通过 docker cp 或 volume)"
    exit 1
fi

# ----------------------
# 3. 动态确定目标路径
# ----------------------

if [ -n "$AGENT_NAME" ]; then
    # 模式 A: 指定了 Agent Profile
    TARGET_DIR="$HERMES_HOME/profiles/$AGENT_NAME/plugins/$HER_PLUGIN"
    ENABLE_CMD="hermes -p $AGENT_NAME plugins enable $HER_PLUGIN"
    echo ">> 模式: Profile [$AGENT_NAME]"
else
    # 模式 B: 默认全局插件
    TARGET_DIR="$HERMES_HOME/plugins/$HER_PLUGIN"
    ENABLE_CMD="hermes plugins enable $HER_PLUGIN"
    echo ">> 模式: Global Default"
fi

echo ">> 目标目录: $TARGET_DIR"

# ----------------------
# 4. 执行部署操作
# ----------------------

# 1. 创建目标目录
mkdir -p "$TARGET_DIR"

# 2. 同步文件 (使用 rsync 或 cp)
# 注意：SRC_PATH 末尾加 / 表示复制目录内容
if command -v rsync &> /dev/null; then
    echo ">> 使用 rsync 同步文件..."
    rsync -av --delete --exclude='node_modules' --exclude='.git' "$SRC_PATH/" "$TARGET_DIR/"
else
    echo ">> 使用 cp 同步文件..."
    # 先清空目标目录以防旧文件残留
    rm -rf "$TARGET_DIR"/*
    cp -rf "$SRC_PATH/"* "$TARGET_DIR/"
fi

# 3. 进入插件目录
cd "$TARGET_DIR"

# 4. 启用插件
echo ">> 启用插件..."
eval "$ENABLE_CMD"


echo "=================================================================="
echo "✅ 部署成功！"
echo "   位置: $TARGET_DIR"
if [ -n "$AGENT_NAME" ]; then
    echo "   Profile: $AGENT_NAME $HER_PLUGIN"
fi
echo "=================================================================="
