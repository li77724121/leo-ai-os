#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🖥️ 多任务监控大屏 — 后端服务
Flask + WebSocket, 提供:
  GET  /                    → 5屏大屏页面
  GET  /api/state           → 聚合状态快照
  GET  /api/events?limit=N  → 最近事件
  WS   /ws                  → 实时事件推送

启动: python3 server.py  (端口 8800)
"""
import os
import json
import time
import threading
from pathlib import Path

from flask import Flask, jsonify, render_template_string
from flask_sock import Sock

import events
import state

BASE = Path(__file__).parent
PORT = 8800

app = Flask(__name__)
app.config["SOCK_SERVER_OPTIONS"] = {"ping_interval": 25}
sock = Sock(app)


# ========== 页面 ==========
INDEX_HTML = None

def load_index():
    global INDEX_HTML
    try:
        INDEX_HTML = (BASE / "web" / "index.html").read_text(encoding="utf-8")
    except Exception:
        INDEX_HTML = "<h1>web/index.html 缺失</h1>"
    return INDEX_HTML


@app.route("/")
def index():
    return render_template_string(load_index())


@app.route("/api/state")
def api_state():
    # 直接读磁盘 state.json (采集器多进程写入, 内存会过期)
    try:
        with open(BASE / "data" / "state.json", "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception:
        return jsonify(state.get_all())


@app.route("/api/events")
def api_events():
    # 直接读磁盘 events.jsonl (采集器多进程写入, 内存缓冲会过期)
    try:
        limit = int(os.environ.get("LIMIT", 200))
        with open(BASE / "data" / "events.jsonl", "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
        evs = [json.loads(l) for l in lines if l.strip()]
        return jsonify({"events": evs})
    except Exception:
        return jsonify({"events": events.recent(200)})


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "time": time.strftime("%Y-%m-%d %H:%M:%S")})


@app.route("/api/ping")
def api_ping():
    """前端心跳, 返回各子系统活跃度"""
    try:
        with open(BASE / "data" / "state.json", "r", encoding="utf-8") as f:
            st = json.load(f)
    except Exception:
        st = state.get_all()
    now = time.time()
    heartbeat = {}
    for k in ("hermes", "zspace", "vscode", "okx", "system", "kb"):
        lu = st.get(k, {}).get("last_update", 0)
        age = now - lu if lu else 999
        heartbeat[k] = {
            "age": round(age, 1),
            "status": "active" if age < 180 else ("slow" if age < 600 else "idle"),
        }
    return jsonify({"heartbeat": heartbeat, "now": now})


# ========== WebSocket ==========
@sock.route("/ws")
def ws_events(ws):
    # 连接后先推历史 (从磁盘读)
    try:
        with open(BASE / "data" / "events.jsonl", "r", encoding="utf-8") as f:
            lines = f.readlines()[-100:]
        for l in lines:
            if l.strip():
                ws.send(json.dumps({"type": "event", "data": json.loads(l)}))
    except Exception:
        pass

    unsub = events.subscribe(lambda ev: _push(ws, ev))
    try:
        while True:
            msg = ws.receive(timeout=30)
            if msg is None:
                break
            # 简单 ping-pong
            ws.send(json.dumps({"type": "pong"}))
    except Exception:
        pass
    finally:
        unsub()


def _push(ws, ev):
    try:
        ws.send(json.dumps({"type": "event", "data": ev}))
    except Exception:
        pass


# ========== 启动 ==========
if __name__ == "__main__":
    state.load()
    # 载入历史事件到缓冲
    for ev in events.load_history(200):
        pass

    print("=" * 55)
    print("🖥️ 多任务监控大屏 后端启动")
    print(f"  页面:  http://127.0.0.1:{PORT}")
    print(f"  状态:  http://127.0.0.1:{PORT}/api/state")
    print(f"  事件:  http://127.0.0.1:{PORT}/api/events")
    print(f"  WS:    ws://127.0.0.1:{PORT}/ws")
    print("=" * 55)
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
