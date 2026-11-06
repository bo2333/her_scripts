#!/usr/bin/env bash
# =============================================================================
# 创建或更新软链接
# 用法: ./create_symlink.sh <源目录> <目标目录>
# 返回值: 0 = 成功, 1 = 失败
# =============================================================================

set -euo pipefail

SOURCE="$1"
TARGET="$2"

# 1. 基本参数检查
if [ -z "$SOURCE" ] || [ -z "$TARGET" ]; then
    echo "[ERROR] 参数不足: $0 <源目录> <目标目录>"
    exit 1
fi

# 统一转为绝对路径，避免相对路径判断失误
SOURCE_ABS=$(cd "$SOURCE" 2>/dev/null && pwd) || {
    echo "[FAIL] 源不存在或不可访问: $SOURCE"
    exit 1
}
TARGET_ABS=$(cd "$(dirname "$TARGET")" 2>/dev/null && pwd)/$(basename "$TARGET") || {
    echo "[FAIL] 目标父目录不可访问: $TARGET"
    exit 1
}

# 2. 检查目标是否已存在（使用 -L 或 -e，注意损坏的软链）
if [ -L "$TARGET_ABS" ]; then
    # 目标是一个软链接，读取它当前指向的路径
    CURRENT_SOURCE=$(readlink -f "$TARGET_ABS" 2>/dev/null || true)
    
    if [ "$CURRENT_SOURCE" = "$SOURCE_ABS" ]; then
        echo "[SUCCESS] 软链接已存在且指向正确: $TARGET_ABS -> $SOURCE_ABS"
        exit 0
    fi

    # 指向错误，删除旧链接
    echo "[INFO] 软链接指向错误，正在删除旧链接: $TARGET_ABS -> $CURRENT_SOURCE"
    rm -f "$TARGET_ABS"
elif [ -e "$TARGET_ABS" ]; then
    # 目标是实体文件或目录，强制删除
    echo "[WARN] 目标是一个实体文件/目录，正在删除: $TARGET_ABS"
    rm -rf "$TARGET_ABS"
fi

# 3. 确保目标父目录存在
mkdir -p "$(dirname "$TARGET_ABS")"

# 4. 创建软链接
if ln -s "$SOURCE_ABS" "$TARGET_ABS"; then
    echo "[SUCCESS] 软链接创建成功: $TARGET_ABS -> $SOURCE_ABS"
    exit 0
else
    echo "[FAIL] 软链接创建失败"
    exit 1
fi