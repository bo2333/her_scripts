#!/bin/bash

# ==============================================================================
# 此脚本必须在容器内部执行！执行额外的插件脚本
# start_plugin_init.sh <plugin> <sh> <profiles> 
# start_plugin_init.sh hermes-lcm ./scripts/install.sh    // 默认 default
# start_plugin_init.sh hermes-lcm ./scripts/install.sh ceo
# ==============================================================================

if [ $# -lt 2 ]; then
    echo "错误: 缺少必要参数" >&2
    echo "用法: $0 <plugin>" >&2
    echo "示例: $0 start_plugin_install.sh hermes-lcm ./scripts/install.sh" >&2
    exit 1
fi

# ----------------------
# 1. 配置区域 (请根据实际情况修改)
# ----------------------
# 获取传入的参数 (如果在容器内执行脚本时传参)
HER_PLUGIN="$1"
SH_PATH="$2"
AGENT_NAME="${3:-}"


# 获取当前用户主目录下的 .hermes 路径
HERMES_HOME="$HOME/.hermes"

# ----------------------
# 3. 动态确定目标路径
# ----------------------

if [ -n "$AGENT_NAME" ]; then
    # 模式 A: 指定了 Agent Profile
    TARGET_DIR="$HERMES_HOME/profiles/$AGENT_NAME/plugins/$HER_PLUGIN"
    echo ">> 模式: Profile [$AGENT_NAME]"
else
    # 模式 B: 默认全局插件
    TARGET_DIR="$HERMES_HOME/plugins/$HER_PLUGIN"
    echo ">> 模式: Global Default"
fi

cd "$TARGET_DIR"


# 5. 执行安装脚本
if [ -f "$SH_PATH" ]; then
    echo ">> 执行 $SH_PATH ..."
    chmod +x $SH_PATH
    eval $SH_PATH
    echo ">> 安装脚本执行完成。"
else
    echo ">> 警告: 未找到 $SH_PATH，跳过。"
fi