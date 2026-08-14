#!/bin/bash
# 多任务监控大屏 - 一键启动/停止
# 用法: ./run_ops_dashboard.sh [start|stop|restart|status]

OPS_DIR="$HOME/leo-ai-os/ops-dashboard"
PIDS_FILE="$OPS_DIR/data/pids"

start() {
  echo "🚀 启动多任务监控大屏..."
  cd "$OPS_DIR"
  
  # 启动 server (端口 8800)
  nohup python3 server.py > logs/server.out 2>&1 &
  echo "server $!" >> "$PIDS_FILE"
  
  # 启动采集器
  for c in collector_hermes collector_okx collector_vscode collector_zspace; do
    nohup python3 "collectors/$c.py" > "logs/$c.out" 2>&1 &
    echo "$!" >> "$PIDS_FILE"
    echo "  ✅ $c"
  done
  
  echo "✅ 全部启动完成"
  echo "📺 打开: http://127.0.0.1:8800"
}

stop() {
  echo "🛑 停止所有进程..."
  if [ -f "$PIDS_FILE" ]; then
    while read pid; do
      kill "$pid" 2>/dev/null
    done < "$PIDS_FILE"
    rm -f "$PIDS_FILE"
  fi
  pkill -f "ops-dashboard/server.py" 2>/dev/null
  pkill -f "ops-dashboard/collectors" 2>/dev/null
  echo "✅ 已停止"
}

status() {
  echo "📊 大屏进程状态:"
  ps aux | grep -E "ops-dashboard" | grep -v grep | awk '{print "  PID", $2, $11, $12}' || echo "  无进程"
}

case "$1" in
  start) start ;;
  stop) stop ;;
  restart) stop; sleep 2; start ;;
  status) status ;;
  *) echo "用法: $0 [start|stop|restart|status]" ;;
esac
