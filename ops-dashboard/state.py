#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗄️ 状态聚合层
各 collector 写入各自状态 → 聚合为统一 state.json
前端 /api/state 获取快照
"""
import json
import time
import threading
from pathlib import Path

BASE = Path(__file__).parent
STATE_FILE = BASE / "data" / "state.json"

_lock = threading.Lock()
_state = {
    "updated": 0,
    "hermes": {"status": "unknown", "last_update": 0},
    "zspace": {"status": "unknown", "last_update": 0},
    "vscode": {"status": "unknown", "last_update": 0},
    "okx": {"status": "unknown", "last_update": 0},
    "system": {"status": "unknown", "last_update": 0},
    "kb": {"status": "unknown", "last_update": 0},
    "heartbeat": {},
}


def update(source, data):
    """更新某子系统状态 (先合并磁盘已有状态, 避免多进程互相覆盖)"""
    global _state
    with _lock:
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                disk_state = json.load(f)
            _state = disk_state
        except Exception:
            pass
        _state[source] = data
        _state[source]["last_update"] = time.time()
        _state["updated"] = time.time()
        _save()
    return data


def get_all():
    with _lock:
        return json.loads(json.dumps(_state))


def get(source):
    with _lock:
        return json.loads(json.dumps(_state.get(source, {})))


def _save():
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(_state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load():
    """启动时从文件恢复"""
    global _state
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            _state = json.load(f)
    except Exception:
        pass
