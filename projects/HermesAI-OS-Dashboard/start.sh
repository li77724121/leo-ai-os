#!/bin/bash
# Leo AI Command Center - 启动脚本
# 用法: ./start.sh [port]

PORT=${1:-4444}
echo "=========================================="
echo "  Leo AI Command Center 启动中..."
echo "=========================================="

# 1. 检查 Node
if ! command -v node &>/dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node 18+"
    exit 1
fi

# 2. 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，安装依赖..."
    npm install --no-audit --no-fund
fi

# 3. 启动开发服务器
echo "🚀 启动 Dashboard..."
echo "🌐 访问地址: http://localhost:${PORT}"
echo "=========================================="
exec npm run dev -- --port ${PORT}
