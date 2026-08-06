#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💰 OKX 交易采集器
从 trading dashboard (http://127.0.0.1:8600/api/status) 读取
→ 更新 state + 发布事件 (成交/挂单变化)
"""
import json
import time
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import events
import state

DASH_URL = "http://127.0.0.1:8600/api/status"
INTERVAL = 15
_last_orders = None
_last_balance = None


def fetch():
    try:
        req = urllib.request.Request(DASH_URL, headers={"User-Agent": "Ops-Dash"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def collect():
    global _last_orders, _last_balance
    d = fetch()
    if "error" in d:
        state.update("okx", {"status": "error", "error": d["error"]})
        events.warn("okx", "network", f"OKX 数据源不可用: {d['error'][:60]}")
        return

    okx_bal = d.get("okx_balance") or {}
    dsb = d.get("ds_balance") or {}
    orders = d.get("orders") or {}

    data = {
        "status": "online",
        "balance": okx_bal.get("total_usd"),
        "sol": d.get("price"),
        "position": d.get("position_usdt"),
        "orders": orders.get("total", 0),
        "grid_status": d.get("grid_status", ""),
        "pnl": d.get("profit", 0),
        "ds_used": dsb.get("used"),
        "ds_avail": dsb.get("available"),
    }
    state.update("okx", data)

    # 事件: 挂单数变化
    cur_orders = orders.get("total", 0)
    if _last_orders is not None and cur_orders != _last_orders:
        events.success("okx", "trade", f"挂单变化: {_last_orders} → {cur_orders}")
    _last_orders = cur_orders

    # 事件: 余额变化
    cur_bal = okx_bal.get("total_usd")
    if _last_balance is not None and cur_bal and abs(cur_bal - _last_balance) > 1:
        events.info("okx", "trade", f"账户余额: ${cur_bal:.2f} (Δ{cur_bal-_last_balance:+.2f})")
    _last_balance = cur_bal


if __name__ == "__main__":
    while True:
        try:
            collect()
        except Exception as e:
            events.error("okx", "system", f"OKX采集失败: {e}")
        time.sleep(INTERVAL)
