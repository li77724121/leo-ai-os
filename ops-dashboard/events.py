#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📡 统一事件总线
各 collector 上报事件 → 写入 events.jsonl + 内存环形缓冲
前端通过 WebSocket 订阅实时事件

事件格式:
{
  "ts": "2026-08-06T13:05:01",
  "source": "hermes|vscode|zspace|okx|system|kb",
  "level": "info|success|warn|error",
  "category": "task|model|trade|file|network|system",
  "message": "人类可读",
  "meta": {}
}
"""
import json
import time
import threading
from pathlib import Path
from collections import deque
from datetime import datetime

BASE = Path(__file__).parent
EVENTS_FILE = BASE / "data" / "events.jsonl"
MAX_MEMORY = 1000   # 内存保留条数

_lock = threading.Lock()
_buffer = deque(maxlen=MAX_MEMORY)
_subscribers = []   # WebSocket 客户端回调

LEVELS = {"info": 0, "success": 1, "warn": 2, "error": 3}


def publish(source, level, category, message, meta=None):
    """发布事件"""
    ev = {
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "source": source,
        "level": level,
        "category": category,
        "message": message,
        "meta": meta or {},
    }
    with _lock:
        _buffer.appendleft(ev)
        # 追加到文件
        try:
            with open(EVENTS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # 通知订阅者
        for cb in list(_subscribers):
            try:
                cb(ev)
            except Exception:
                pass
    return ev


def subscribe(cb):
    """注册 WebSocket 推送回调, 返回退订函数"""
    with _lock:
        _subscribers.append(cb)
    return lambda: _unsubscribe(cb)


def _unsubscribe(cb):
    with _lock:
        if cb in _subscribers:
            _subscribers.remove(cb)


def recent(limit=200):
    """获取最近事件"""
    with _lock:
        return list(_buffer)[:limit]


def load_history(limit=100):
    """从文件加载历史事件 (启动时用)"""
    try:
        lines = []
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
        return [json.loads(l) for l in lines if l.strip()]
    except Exception:
        return []


# 便捷方法
def info(source, category, message, meta=None):
    return publish(source, "info", category, message, meta)


def success(source, category, message, meta=None):
    return publish(source, "success", category, message, meta)


def warn(source, category, message, meta=None):
    return publish(source, "warn", category, message, meta)


def error(source, category, message, meta=None):
    return publish(source, "error", category, message, meta)
