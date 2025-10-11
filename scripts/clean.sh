#!/bin/bash
# 项目清理脚本 - 删除临时文件和缓存

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🧹 开始清理项目..."

# 清理 Python 缓存
echo "📦 清理 Python 缓存文件..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true

# 清理 egg-info
echo "🥚 清理 egg-info..."
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true

# 清理构建文件
echo "🏗️  清理构建文件..."
rm -rf build/ dist/ .eggs/ 2>/dev/null || true

# 清理测试缓存
echo "🧪 清理测试缓存..."
rm -rf .pytest_cache/ .coverage htmlcov/ .tox/ 2>/dev/null || true

# 清理系统文件
echo "💻 清理系统文件..."
find . -type f -name ".DS_Store" -delete 2>/dev/null || true
find . -type f -name "Thumbs.db" -delete 2>/dev/null || true

# 清理临时文件
echo "📄 清理临时文件..."
find . -type f -name "*.tmp" -delete 2>/dev/null || true
find . -type f -name "*.log" -delete 2>/dev/null || true

# 清理 uploads 目录（保留目录本身）
if [ -d "uploads" ]; then
    echo "📤 清理 uploads 目录..."
    rm -rf uploads/*
fi

# 可选：清理 outputs 目录（注释掉以保留输出）
# if [ -d "outputs" ]; then
#     echo "📊 清理 outputs 目录..."
#     rm -rf outputs/*
# fi

echo "✅ 清理完成！"
echo ""
echo "已清理："
echo "  - Python 缓存文件 (__pycache__, *.pyc)"
echo "  - Egg-info 文件"
echo "  - 构建文件 (build/, dist/)"
echo "  - 测试缓存"
echo "  - 系统文件 (.DS_Store, Thumbs.db)"
echo "  - 临时文件 (*.tmp, *.log)"
echo "  - uploads/ 目录内容"
echo ""
echo "💡 提示：outputs/ 目录已保留。如需清理，请取消脚本中的注释。"
