#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抄币状态 → Telegram 推送
从大屏 API 读取实时数据, 推送到用户的 Telegram bot (@CEOleo_bot)
- 每 N 分钟推送一次状态卡片
- 支持手动触发: python3 push_status.py
- 支持 --force 强制推送
"""
import os
import sys
import json
import time
import argparse
import urllib.request
from datetime import datetime

# ========== 配置 ==========
DASHBOARD_URL = "http://127.0.0.1:8600/api/status"

def load_env(path):
    """加载 .env 文件"""
    env = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    except Exception:
        pass
    return env

def get_telegram_config():
    """从多个位置查找 Telegram 配置"""
    # 1. 环境变量
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_HOME_CHANNEL") or os.getenv("TELEGRAM_CHAT_ID")
    
    # 2. Hermes .env
    if not token or not chat:
        env = load_env(os.path.expanduser("~/.hermes/.env"))
        token = token or env.get("TELEGRAM_BOT_TOKEN")
        chat = chat or env.get("TELEGRAM_HOME_CHANNEL") or env.get("TELEGRAM_CHAT_ID")
    
    # 3. 交易目录 .env
    if not token or not chat:
        env = load_env(os.path.expanduser("~/leo-ai-os/trading_bot/.env"))
        token = token or env.get("TELEGRAM_BOT_TOKEN")
        chat = chat or env.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_HOME_CHANNEL")
    
    return token, chat

def fetch_dashboard():
    """从大屏 API 获取数据"""
    try:
        req = urllib.request.Request(DASHBOARD_URL, headers={"User-Agent": "Hermes-Push"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def format_message(data):
    """格式化为 Telegram 消息"""
    if "error" in data:
        return f"⚠️ 大屏API不可用: {data['error']}"
    
    price = data.get("price")
    pos = data.get("position_usdt", 0)
    orders = data.get("orders", {})
    total = orders.get("total", 0)
    buy = orders.get("buy", 0)
    sell = orders.get("sell", 0)
    status = data.get("grid_status") or "未知"
    updated = data.get("last_update") or "—"
    events = data.get("events", [])
    model_stats = data.get("model_stats", {})
    okx = data.get("okx_balance") or {}
    dsb = data.get("ds_balance") or {}

    # 最近错误统计
    recent_err = sum(1 for e in events if "ERROR" in e or "异常" in e)

    # 盈亏 - 尝试从事件流估算 (简化: 用持仓变化)
    profit = data.get("profit", 0)

    lines = [
        "🟢 **抄币监控 | 实时状态**",
        "━━━━━━━━━━━━━━",
        f"💰 **SOL 现价**: ${price if price else '—'}",
        f"🏦 **OKX 账户**: ${okx.get('total_usd', 0):,.2f}" if okx.get("total_usd") else f"📦 **持仓价值**: ${pos:.2f} USDT",
        f"📋 **挂单**: {total} 个" + (f" (买{buy}/卖{sell})" if (buy or sell) else ""),
        f"📊 **网格状态**: {status}",
        "",
        f"🕒 最后更新: {updated}",
    ]

    if profit:
        lines.insert(4, f"📈 **累计盈亏**: {'+' if profit > 0 else ''}{profit:.2f} USDT")

    # 模型消耗 (真实账户 + 当前调用)
    last_m = model_stats.get("last")
    if dsb or last_m:
        ai_lines = ["", "🤖 **AI 消耗**"]
        if last_m:
            ai_lines.append(f"🧠 **当前模型**: {last_m.get('model', '—')} ({last_m.get('provider', '—')})")
        if dsb.get("total") is not None:
            ai_lines.append(f"🔴 **DeepSeek**: 已用 ¥{dsb.get('used', 0):.2f} / 可用 ¥{dsb.get('available', 0):.2f}"
                            + (" ⚠️ 余额不足!" if dsb.get("available", 0) < 10 else ""))
        lines.extend(ai_lines)

    if recent_err > 0:
        lines.append(f"⚠️ 近况: 最近事件流含 {recent_err} 条错误 (可能网络波动)")
    
    lines.append(f"🔗 大屏: http://192.168.0.102:8600")
    
    return "\n".join(lines)

def send_telegram(token, chat_id, text):
    """发送 Telegram 消息"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "User-Agent": "Hermes-Push"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("ok", False), result
    except Exception as e:
        return False, {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="抄币状态推送到 Telegram")
    parser.add_argument("--force", action="store_true", help="强制推送(忽略时间间隔)")
    parser.add_argument("--interval", type=int, default=1800, help="最小推送间隔秒数(默认1800=30分钟)")
    args = parser.parse_args()
    
    # 时间间隔控制文件
    state_file = os.path.expanduser("~/leo-ai-os/trading_bot/.push_state")
    
    if not args.force and os.path.exists(state_file):
        try:
            last = float(open(state_file).read().strip())
            if time.time() - last < args.interval:
                return  # 未到时间, 静默退出
        except Exception:
            pass
    
    token, chat = get_telegram_config()
    if not token or not chat:
        print("❌ 未找到 Telegram 配置")
        sys.exit(1)
    
    data = fetch_dashboard()
    msg = format_message(data)
    ok, resp = send_telegram(token, chat, msg)
    
    if ok:
        # 记录推送时间
        with open(state_file, "w") as f:
            f.write(str(time.time()))
        print(f"✅ 已推送 ({datetime.now().strftime('%H:%M:%S')})")
    else:
        print(f"❌ 推送失败: {resp}")

if __name__ == "__main__":
    main()
