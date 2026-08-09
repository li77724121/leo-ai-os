#!/bin/bash
# LeoDesignerAI - 一键启动脚本
# Mac Mini M1 上双击运行

echo "============================="
echo "  Leo Designer AI Server"
echo "  v1.0 MVP"
echo "============================="
echo ""

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$BASE_DIR/backend"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要安装 Python 3.9+"
    echo "   下载: https://www.python.org/downloads/"
    read -p "按回车退出..."
    exit 1
fi

echo "✅ Python: $(python3 --version)"

# 安装依赖
echo ""
echo "📦 安装后端依赖..."
cd "$BACKEND_DIR"
pip3 install -r requirements.txt -q 2>&1 | tail -1
echo "✅ 依赖安装完成"

# 启动后端
echo ""
echo "🚀 启动 AI Server (端口 8000)..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"

# 等待启动
sleep 2

# 健康检查
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
if [ "$HEALTH" = "200" ]; then
    echo "✅ 后端运行中: http://localhost:8000"
    echo ""
    echo "📱 APP连接地址: http://localhost:8000"
    echo "📝 API文档: http://localhost:8000/docs"
else
    echo "⚠️ 后端启动中，请稍后..."
fi

echo ""
echo "============================="
echo "  按 Ctrl+C 停止服务器"
echo "============================="

# 等待后台进程
wait $BACKEND_PID
