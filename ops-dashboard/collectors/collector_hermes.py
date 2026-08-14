#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Hermes 状态采集器
从 model_stats.json + agent.log 读取 → 更新 state + 发布事件
"""
import json
import time
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import events
import state

BASE = Path(__file__).parent.parent
MODEL_STATS = BASE / "trading_bot" / "model_stats.json" if (BASE / "trading_bot" / "model_stats.json").exists() else Path.home() / "leo-ai-os" / "trading_bot" / "model_stats.json"
AGENT_LOG = Path.home() / ".hermes" / "logs" / "agent.log"

INTERVAL = 30  # 采集间隔秒


def read_model_stats():
    try:
        return json.loads(MODEL_STATS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_agent_activity():
    """读取 agent.log 尾部, 检测最近活跃"""
    try:
        with open(AGENT_LOG, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 50000))
            tail = f.read()
        # 最后 API call 时间
        times = re.findall(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?API call", tail)
        last_api = times[-1] if times else ""
        return last_api
    except Exception:
        return ""


def collect():
    ms = read_model_stats()
    last_api = read_agent_activity()

    data = {
        "status": "online",
        "models": ms.get("calls", 0),
        "tokens": (ms.get("tokens") or {}).get("total", 0),
        "cost": (ms.get("cost") or {}).get("total", 0.0),
        "model": (ms.get("last") or {}).get("model", ""),
        "model_sub": f"{(ms.get('last') or {}).get('provider', '')} · {(ms.get('last') or {}).get('time', '')}",
        "tasks": "3待办",
        "last_api": last_api,
    }
    state.update("hermes", data)

    # 事件: 新模型调用 (模型变化时)
    last_model = (ms.get("last") or {}).get("model", "")
    if last_model:
        events.info("hermes", "model", f"模型调用: {last_model}")


if __name__ == "__main__":
    while True:
        try:
            collect()
        except Exception as e:
            events.error("hermes", "system", f"Hermes采集失败: {e}")
        time.sleep(INTERVAL)
