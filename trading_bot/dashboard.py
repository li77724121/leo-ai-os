#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes AI OS - 综合监控大屏 V2 (融合 Notion 大屏提示词)
模块:
  1. 交易监控中心 (OKX SOL 网格) - 实时
  2. AI任务市场 (Task Marketplace) - 配置+实时
  3. 智能模型调度中心 V2 - 配置
  4. Global AI Cloud - 状态探测
  5. AI成本财务中心 - 配置+实时
  6. 项目管理 - 配置
  7. 交易AI中心 (BTC分析) - 配置
低资源占用: 单文件 Flask, 无数据库
"""
import os
import re
import json
import time
import socket
import threading
import urllib.request
from datetime import datetime
from collections import deque
from pathlib import Path

from flask import Flask, jsonify, render_template_string

# ==================== 配置 ====================
BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "grid_trader.log"
PORT = 8600
REFRESH_MS = 3000

app = Flask(__name__)

# ==================== 静态配置数据 (来自 Notion 大屏提示词) ====================
TASK_MARKET = {
    "开发APP": {"stars": 5, "desc": "开发APP", "agent": "engineer", "model": "laguna-s-2.1:free", "device": "Mac mini"},
    "整理资料": {"stars": 2, "desc": "整理资料", "agent": "secretary", "model": "ling-3.0-flash:free", "device": "MacBook"},
    "分析市场": {"stars": 4, "desc": "分析市场", "agent": "analyst", "model": "nemotron-ultra:free", "device": "Cloud"},
    "交易监控": {"stars": 5, "desc": "交易监控", "agent": "trader", "model": "deepseek-v4-flash", "device": "Mac mini"},
}

MODEL_DISPATCH = [
    {"task": "写Swift代码", "local": "qwen2.5-coder", "local_speed": "8s", "cloud": "Ling Flash", "cloud_speed": "2s", "choice": "Ling Flash"},
    {"task": "中文整理", "local": "qwen2.5:7b", "local_speed": "5s", "cloud": "Ling Flash", "cloud_speed": "2s", "choice": "Ling Flash"},
    {"task": "复杂分析", "local": "—(超载)", "local_speed": "—", "cloud": "nemotron-ultra", "cloud_speed": "3s", "choice": "nemotron-ultra"},
]

AI_CLOUD = [
    {"name": "OpenRouter", "region": "USA", "role": "云路由", "icon": "🌐"},
    {"name": "NVIDIA Cloud", "region": "USA", "role": "推理", "icon": "🟢"},
    {"name": "DeepSeek", "region": "China", "role": "关键任务", "icon": "🔴", "note": "付费,仅关键任务"},
    {"name": "Local Ollama", "region": "Leo Home", "role": "本地兜底", "icon": "💻"},
]

COST_CENTER = {
    "today": {"openrouter": 0.18, "ollama": 0.0, "server": 0.0, "deepseek": 0.0},
    "monthly": {"ai_cost": 12.0, "income": 0.0, "roi": "—"},
}

PROJECTS = [
    {"name": "PowerAI", "status": "开发中", "icon": "⚡"},
    {"name": "AI制图", "status": "MVP", "icon": "🎨"},
    {"name": "Token充值平台", "status": "规划", "icon": "💳"},
    {"name": "翻译助手", "status": "开发", "icon": "🌏"},
]

TRADE_AI = {
    "symbol": "BTC",
    "trend": "上涨",
    "risk": "中",
    "advice": "等待",
    "note": "策略测试中",
}

DAILY_REPORT = {
    "date": "2026-08-06",
    "done": ["Dashboard V2", "Hermes升级"],
    "running": "Mac mini 24小时",
    "cost": 0.25,
    "suggestion": "开发PowerAI MVP",
}

# ==================== 实时数据缓存 ====================
_cache = {
    "price": None,
    "position_usdt": 0.0,
    "orders": {"buy": 0, "sell": 0, "total": 0},
    "grid_status": "未知",
    "last_update": None,
    "profit": 0.0,
    "events": deque(maxlen=100),
    "last_pos": 0,
    "cache_time": 0,
    "cloud_status": {},   # 模型云探测结果
    "model_stats": {},    # 模型调用统计
    "model_cache_time": 0,
    "fx_rate": 7.10,
    "fx_time": 0,
    "okx_balance": None,
    "okx_time": 0,
    "ds_balance": None,
    "ds_time": 0,
}

AGENT_LOG = Path.home() / ".hermes" / "logs" / "agent.log"
MODEL_STATS_FILE = BASE_DIR / "model_stats.json"   # Hermes cron 生成的统计 (launchd 无权读 ~/.hermes)
ENV_FILE = BASE_DIR / ".env"   # OKX API keys

# DeepSeek 官方定价 (CNY/M tokens) — 2026-08-06 查自 platform.deepseek.com
DS_PRICE_IN_MISS = 1.0        # 缓存未命中输入 (元/M)
DS_PRICE_IN_HIT = 0.02        # 缓存命中输入 (元/M)
DS_PRICE_OUT = 2.0            # 输出 (元/M)


def load_trading_env():
    """读取交易 .env (OKX keys), 供余额查询"""
    env = {}
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"')
    except Exception:
        pass
    return env


def check_host(host, port, timeout=3):
    """探测主机连通性"""
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def probe_cloud():
    """探测各 AI 云可用性 (轻量, 带缓存)"""
    now = time.time()
    if now - _cache.get("probe_time", 0) < 60:
        return _cache["cloud_status"]
    _cache["probe_time"] = now

    status = {}
    # OpenRouter API
    try:
        req = urllib.request.Request("https://openrouter.ai/api/v1/models",
                                     headers={"User-Agent": "Hermes-Dash"})
        with urllib.request.urlopen(req, timeout=4) as r:
            status["openrouter"] = "🟢 可用" if r.status == 200 else "🟡 异常"
    except Exception:
        status["openrouter"] = "🔴 离线"

    # 本地 Ollama
    status["ollama"] = "🟢 可用" if check_host("127.0.0.1", 11434) else "🔴 离线"

    # DeepSeek (有 API key 才算可用)
    status["deepseek"] = "🟢 已配置" if os.getenv("DEEPSEEK_API_KEY") else "🟡 未配置"

    # Mac mini
    status["macmini"] = "🟢 在线" if check_host("192.168.110.47", 22, timeout=2) else "🟡 不可达"

    _cache["cloud_status"] = status
    return status


# ===== 汇率 (USD→CNY), 1 小时缓存 =====
def get_usd_cny():
    """获取 USD→CNY 汇率, 失败时用默认值 7.1"""
    now = time.time()
    if _cache.get("fx_time", 0) and now - _cache["fx_time"] < 3600:
        return _cache["fx_rate"]
    rate = 7.10  # 默认
    for url in ("https://open.er-api.com/v6/latest/USD",
                "https://api.exchangerate-api.com/v4/latest/USD"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as r:
                d = json.loads(r.read())
                cny = d.get("rates", {}).get("CNY")
                if cny:
                    rate = float(cny)
                    break
        except Exception:
            continue
    _cache["fx_time"] = now
    _cache["fx_rate"] = rate
    return rate


# ===== DeepSeek 真实账户余额, 5 分钟缓存 =====
def get_deepseek_balance():
    """查询 DeepSeek 平台真实余额 (元), 失败返回 None"""
    now = time.time()
    if _cache.get("ds_time", 0) and now - _cache["ds_time"] < 300:
        return _cache["ds_balance"]
    _cache["ds_time"] = now

    env = load_trading_env()
    ds_key = env.get("DEEPSEEK_API_KEY") or env.get("DEEPSEEK_KEY")
    # 也查 Hermes 环境
    if not ds_key:
        try:
            env2 = {}
            for line in Path.home().joinpath(".hermes/.env").read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env2[k.strip()] = v.strip().strip('"')
            ds_key = env2.get("DEEPSEEK_API_KEY") or env2.get("DEEPSEEK_KEY")
        except Exception:
            pass

    if not ds_key:
        _cache["ds_balance"] = None
        return None

    try:
        req = urllib.request.Request("https://api.deepseek.com/user/balance", headers={
            "Authorization": "Bearer " + ds_key,
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        infos = d.get("balance_infos", [])
        if infos:
            b = infos[0]
            _cache["ds_balance"] = {
                "currency": b.get("currency", "CNY"),
                "total": float(b.get("total_balance", 0)),
                "available": float(b.get("granted_balance", 0)),
                "used": float(b.get("topped_up_balance", 0)),
                "ts": datetime.now().strftime("%H:%M:%S"),
            }
            return _cache["ds_balance"]
    except Exception:
        pass
    _cache["ds_balance"] = None
    return None


# ===== OKX 真实账户余额, 60s 缓存 =====
def get_okx_balance():
    """查询 OKX 账户真实总估值 (USD), 失败返回 None"""
    now = time.time()
    if _cache.get("okx_time", 0) and now - _cache["okx_time"] < 60:
        return _cache["okx_balance"]
    _cache["okx_time"] = now

    env = load_trading_env()
    api_key = env.get("OKX_API_KEY")
    secret = env.get("OKX_SECRET_KEY")
    passphrase = env.get("OKX_PASSPHRASE")
    if not (api_key and secret and passphrase):
        _cache["okx_balance"] = None
        return None

    # 设置代理 (OKX 国内需代理)
    proxy = env.get("HTTPS_PROXY") or env.get("https_proxy")
    if proxy:
        os.environ["https_proxy"] = proxy
        os.environ["http_proxy"] = proxy.replace("https://", "http://")

    try:
        import base64
        import hmac
        ts = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        path = "/api/v5/account/balance"
        msg = ts + "GET" + path
        sig = base64.b64encode(hmac.new(secret.encode(), msg.encode(), "sha256").digest()).decode()
        req = urllib.request.Request("https://www.okx.com" + path, headers={
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-SIGN": sig,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": passphrase,
            "User-Agent": "Mozilla/5.0",
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        if d.get("code") == "0":
            total_eq = float(d["data"][0].get("totalEq", 0))
            _cache["okx_balance"] = {"total_usd": round(total_eq, 2),
                                     "ts": datetime.now().strftime("%H:%M:%S")}
            return _cache["okx_balance"]
    except Exception:
        pass
    _cache["okx_balance"] = None
    return None


def parse_log():
    """增量解析交易日志"""
    if not LOG_FILE.exists():
        return

    now = time.time()
    if now - _cache["cache_time"] < 2:
        return
    _cache["cache_time"] = now

    _cache["orders"]["buy"] = 0
    _cache["orders"]["sell"] = 0

    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            if _cache["last_pos"] == 0:
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - 30000))
                _cache["last_pos"] = f.tell()
            f.seek(_cache["last_pos"])
            new_lines = f.readlines()
            _cache["last_pos"] = f.tell()
    except Exception:
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                new_lines = f.readlines()
                _cache["last_pos"] = f.tell()
        except Exception:
            return

    for line in new_lines:
        line = line.strip()
        if not line:
            continue

        m = re.search(r"SOL=\$([\d.]+)", line)
        if m:
            _cache["price"] = float(m.group(1))

        m = re.search(r"持仓:\s*\$([\d.]+)", line)
        if m:
            _cache["position_usdt"] = float(m.group(1))

        m = re.search(r"挂单:\s*(\d+)个", line)
        if m:
            _cache["orders"]["total"] = int(m.group(1))

        m = re.search(r"网格完成:\s*(\d+)买单\s*\+\s*(\d+)卖单", line)
        if m:
            _cache["orders"]["buy"] = int(m.group(1))
            _cache["orders"]["sell"] = int(m.group(2))

        for kw, status in [
            ("网格就绪", "就绪 · 等待成交"),
            ("重建网格", "重建中"),
            ("已达最大持仓限制", "已达持仓上限 · 暂停开单"),
            ("止损", "⚠️ 触发止损"),
            ("止盈", "✅ 触发止盈"),
        ]:
            if kw in line:
                _cache["grid_status"] = status
                break

        m = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if m:
            _cache["last_update"] = m.group(1)

        if any(k in line for k in ("ERROR", "异常", "失败", "止损", "止盈", "✅ 挂买单", "✅ 挂卖单")):
            _cache["events"].append(line)


def parse_agent_log():
    """读取 Hermes cron 生成的 model_stats.json (launchd 无法读 ~/.hermes 的 agent.log)"""
    now = time.time()
    if now - _cache.get("model_cache_time", 0) < 30:
        return _cache["model_stats"]
    _cache["model_cache_time"] = now

    stats = {
        "calls": 0,
        "by_provider": {},
        "by_model": {},
        "last": None,
        "deepseek": {"in": 0, "out": 0, "calls": 0, "cost": 0.0},
        "tokens": {"in": 0, "out": 0, "total": 0},
        "cost": {"deepseek": 0.0, "openrouter": 0.0, "local": 0.0, "total": 0.0},
    }

    try:
        with open(MODEL_STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        stats["calls"] = data.get("calls", 0)
        stats["by_provider"] = data.get("by_provider", {})
        stats["by_model"] = data.get("by_model", {})
        stats["last"] = data.get("last")
        stats["deepseek"] = data.get("deepseek", stats["deepseek"])
        stats["tokens"] = data.get("tokens", {"in": 0, "out": 0, "total": 0})
        stats["cost"] = data.get("cost", {"deepseek": 0.0, "openrouter": 0.0, "local": 0.0, "total": 0.0})
    except Exception:
        pass

    _cache["model_stats"] = stats
    return stats


# ==================== 页面 ====================
INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎯 综合监控大屏 | Hermes AI OS</title>
<style>
:root {
  --bg: #020617; --card: #0f172a; --border: #1e293b;
  --text: #e2e8f0; --dim: #64748b;
  --green: #10b981; --red: #ef4444; --blue: #0ea5e9; --yellow: #f59e0b; --purple: #8b5cf6;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { background:var(--bg); color:var(--text); font-family:-apple-system,"PingFang SC","Helvetica Neue",sans-serif; min-height:100vh; padding:20px; }
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; padding-bottom:14px; border-bottom:1px solid var(--border); }
.header h1 { font-size:26px; font-weight:700; }
.header h1 span { color:var(--blue); }
.live { display:inline-flex; align-items:center; gap:6px; background:rgba(16,185,129,.1); color:var(--green); padding:6px 14px; border-radius:20px; font-size:13px; font-weight:600; }
.live .dot { width:8px; height:8px; border-radius:50%; background:var(--green); animation:pulse 1.5s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.time { color:var(--dim); font-size:13px; }

.section-title { font-size:15px; font-weight:700; color:var(--blue); margin:22px 0 12px; letter-spacing:1px; display:flex; align-items:center; gap:8px; }
.section-title::after { content:''; flex:1; height:1px; background:var(--border); }

.grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:14px; }
.card { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px; }
.card .label { color:var(--dim); font-size:12px; margin-bottom:6px; }
.card .value { font-size:28px; font-weight:700; }
.card .sub { color:var(--dim); font-size:11px; margin-top:4px; }
.green { color:var(--green); } .red { color:var(--red); } .blue { color:var(--blue); } .yellow { color:var(--yellow); } .purple { color:var(--purple); }

.status-bar { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px 18px; margin:14px 0; display:flex; justify-content:space-between; align-items:center; }
.status-bar .status { font-size:15px; font-weight:600; }

/* 任务市场 */
.task-row { display:flex; align-items:center; gap:12px; padding:10px 14px; border-bottom:1px solid #16213a; }
.task-row:last-child { border-bottom:none; }
.task-name { flex:1; font-weight:600; font-size:14px; }
.task-stars { color:var(--yellow); font-size:13px; letter-spacing:2px; }
.task-meta { color:var(--dim); font-size:11px; }
.task-badge { padding:2px 10px; border-radius:10px; font-size:11px; font-weight:600; }
.badge-5 { background:rgba(16,185,129,.15); color:var(--green); }
.badge-4 { background:rgba(14,165,233,.15); color:var(--blue); }
.badge-2 { background:rgba(100,116,139,.15); color:var(--dim); }

/* 模型调度 */
.dispatch-table { width:100%; border-collapse:collapse; font-size:13px; }
.dispatch-table th { color:var(--dim); text-align:left; padding:8px 10px; border-bottom:1px solid var(--border); font-weight:600; }
.dispatch-table td { padding:8px 10px; border-bottom:1px solid #16213a; }
.dispatch-table .choice { color:var(--green); font-weight:700; }

/* AI Cloud */
.cloud-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px; }
.cloud-card { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:14px; }
.cloud-card .name { font-weight:700; font-size:14px; display:flex; align-items:center; gap:8px; }
.cloud-card .region { color:var(--dim); font-size:11px; margin-top:4px; }
.cloud-card .status { margin-top:8px; font-size:12px; font-weight:600; }

/* 成本 */
.cost-today { display:grid; grid-template-columns:repeat(auto-fit, minmax(140px,1fr)); gap:10px; margin-bottom:12px; }
.cost-item { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:12px; text-align:center; }
.cost-item .v { font-size:20px; font-weight:700; }
.cost-item .l { color:var(--dim); font-size:11px; margin-top:4px; }

/* 项目 */
.project-row { display:flex; align-items:center; gap:10px; padding:9px 12px; border-bottom:1px solid #16213a; }
.project-row:last-child { border-bottom:none; }
.project-name { flex:1; font-size:13px; font-weight:600; }
.project-status { padding:2px 10px; border-radius:10px; font-size:11px; font-weight:600; }
.st-dev { background:rgba(16,185,129,.15); color:var(--green); }
.st-mvp { background:rgba(139,92,246,.15); color:var(--purple); }
.st-plan { background:rgba(245,158,11,.15); color:var(--yellow); }

/* 事件流 */
.events { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px; margin-top:16px; }
.events h3 { font-size:13px; color:var(--dim); margin-bottom:10px; }
.event-list { max-height:220px; overflow-y:auto; font-size:12px; }
.event-list .ev { padding:5px 0; border-bottom:1px solid #16213a; display:flex; gap:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.event-list .ev .t { color:var(--dim); flex-shrink:0; }
.event-list .ev .m { overflow:hidden; text-overflow:ellipsis; }
.err { color:var(--red) !important; }

/* 双栏 */
.two-col { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
@media (max-width: 900px) { .two-col { grid-template-columns:1fr; } }

/* ===== 活跃度特效 ===== */
@keyframes glowPulse {
  0%, 100% { box-shadow: 0 0 6px rgba(16,185,129,.35), 0 0 18px rgba(16,185,129,.15); border-color: rgba(16,185,129,.55); }
  50% { box-shadow: 0 0 14px rgba(16,185,129,.65), 0 0 34px rgba(16,185,129,.3); border-color: rgba(16,185,129,.9); }
}
@keyframes glowPulseRed {
  0%, 100% { box-shadow: 0 0 6px rgba(239,68,68,.35), 0 0 18px rgba(239,68,68,.15); border-color: rgba(239,68,68,.55); }
  50% { box-shadow: 0 0 14px rgba(239,68,68,.65), 0 0 34px rgba(239,68,68,.3); border-color: rgba(239,68,68,.9); }
}
@keyframes glowPulseBlue {
  0%, 100% { box-shadow: 0 0 6px rgba(14,165,233,.35), 0 0 18px rgba(14,165,233,.15); border-color: rgba(14,165,233,.55); }
  50% { box-shadow: 0 0 14px rgba(14,165,233,.65), 0 0 34px rgba(14,165,233,.3); border-color: rgba(14,165,233,.9); }
}
@keyframes scanline {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(400%); }
}
@keyframes radar {
  0% { transform: scale(.6); opacity: .8; }
  100% { transform: scale(1.8); opacity: 0; }
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: .25; }
}
@keyframes rainbow {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}

/* 活跃卡片: 呼吸发光边框 */
.card.active, .cloud-card.active, .events.active, .status-bar.active {
  animation: glowPulse 1.6s ease-in-out infinite;
}
.card.active-blue { animation: glowPulseBlue 1.8s ease-in-out infinite; }
.card.active-red { animation: glowPulseRed 1.4s ease-in-out infinite; }
/* 空闲模块: 轻微暗化 */
.card.idle, .cloud-card.idle { opacity: .72; filter: saturate(.75); }

/* 活跃徽章 */
.badge-active {
  display:inline-flex; align-items:center; gap:4px;
  background: rgba(16,185,129,.15); color: var(--green);
  font-size:10px; font-weight:700; padding:2px 8px; border-radius:8px;
  animation: blink 1.2s infinite;
}
.badge-idle {
  display:inline-flex; align-items:center; gap:4px;
  background: rgba(100,116,139,.12); color: var(--dim);
  font-size:10px; font-weight:700; padding:2px 8px; border-radius:8px;
}
.badge-idle .dot, .badge-active .dot { width:6px; height:6px; border-radius:50%; display:inline-block; }
.badge-active .dot { background: var(--green); }
.badge-idle .dot { background: var(--dim); }

/* 扫描线特效 (活跃卡片背景) */
.scan-wrap { position:relative; overflow:hidden; }
.scan-wrap.active::after {
  content:''; position:absolute; top:0; left:0; right:0; height:40px;
  background: linear-gradient(to bottom, transparent, rgba(16,185,129,.12), transparent);
  animation: scanline 2.2s linear infinite;
  pointer-events:none;
}

/* 标题流光 */
.title-glow {
  background: linear-gradient(90deg, #0ea5e9, #10b981, #8b5cf6, #f59e0b, #0ea5e9);
  background-size: 200% auto;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  animation: rainbow 4s linear infinite;
}

/* 雷达波纹 */
.radar-dot { position:relative; }
.radar-dot::before {
  content:''; position:absolute; left:50%; top:50%; width:14px; height:14px;
  margin:-7px 0 0 -7px; border-radius:50%;
  background: rgba(16,185,129,.5); animation: radar 1.4s ease-out infinite;
}

/* 模块标题行: 标题 + 活跃徽章 */
.section-head { display:flex; align-items:center; gap:10px; margin:22px 0 12px; }
.section-head h3 { font-size:15px; font-weight:700; color:var(--blue); letter-spacing:1px; margin:0; }
.section-head::after { content:''; flex:1; height:1px; background:var(--border); }

/* 心跳波纹 */
.heartbeat { display:inline-block; animation: blink 1s infinite; }

/* 日报 */
.daily-box { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px; font-size:13px; line-height:2; }
.daily-box .done { color:var(--green); }
</style>
</head>
<body>

<div class="header">
  <h1 class="title-glow">🎯 综合监控大屏 | Hermes AI OS V2</h1>
  <div style="display:flex;align-items:center;gap:14px;">
    <span class="live"><span class="dot"></span> <span id="live_txt">实时</span></span>
    <span class="time" id="upd">—</span>
  </div>
</div>

<!-- ① 交易监控 -->
<div class="section-head">
  <h3>📈 交易监控中心 (OKX SOL 网格)</h3>
  <span class="badge-idle" id="badge_trade"><span class="dot"></span> 等待</span>
</div>
<div class="grid scan-wrap" id="wrap_trade">
  <div class="card"><div class="label">SOL 现价</div><div class="value blue" id="price">—</div><div class="sub">USDT</div></div>
  <div class="card"><div class="label">账户总余额 (OKX)</div><div class="value" id="pos">—</div><div class="sub">≈ <span id="pos_cny">—</span> 元</div></div>
  <div class="card"><div class="label">挂单总数</div><div class="value" id="orders">—</div><div class="sub">买 <span id="buy">—</span> / 卖 <span id="sell">—</span></div></div>
  <div class="card"><div class="label">累计盈亏</div><div class="value" id="profit">—</div><div class="sub">USDT (估算)</div></div>
</div>
<div class="status-bar" id="statusbar">
  <div class="status"><span id="status_icon">⏳</span> <span id="status">读取中...</span></div>
  <div class="time" id="heartbeat">—</div>
</div>

<div class="two-col">
  <!-- ② AI任务市场 -->
  <div>
    <div class="section-head">
      <h3>🧠 AI任务市场</h3>
      <span class="badge-idle" id="badge_tasks"><span class="dot"></span> 待命</span>
    </div>
    <div class="card scan-wrap" style="padding:8px 0;" id="task_market">加载中...</div>
  </div>
  <!-- ③ 智能模型调度中心 -->
  <div>
    <div class="section-title">⚙️ 智能模型调度中心 V2</div>
    <div class="card" style="padding:8px 0; overflow-x:auto;" id="dispatch">加载中...</div>
  </div>
</div>

<!-- ④ Global AI Cloud -->
<div class="section-head">
  <h3>🌐 Global AI Cloud</h3>
  <span class="badge-idle" id="badge_cloud"><span class="dot"></span> 探测中</span>
</div>
<div class="cloud-grid" id="cloud">加载中...</div>

<div class="two-col">
  <!-- ⑤ AI成本财务中心 -->
  <div>
    <div class="section-title">💰 AI成本财务中心</div>
    <div class="cost-today" id="cost">加载中...</div>
  </div>
  <!-- ⑥ 项目管理 -->
  <div>
    <div class="section-title">📋 项目管理</div>
    <div class="card" style="padding:8px 0;" id="projects">加载中...</div>
  </div>
</div>

<div class="two-col">
  <!-- ⑦ 交易AI中心 -->
  <div>
    <div class="section-head">
      <h3>🤖 交易AI中心</h3>
      <span class="badge-idle" id="badge_ai"><span class="dot"></span> 待命</span>
    </div>
    <div class="card" id="trade_ai">加载中...</div>
  </div>
  <!-- ⑨ 模型调用监控 (新增) -->
  <div>
    <div class="section-head">
      <h3>🧬 模型调用监控 (实时)</h3>
      <span class="badge-idle" id="badge_model"><span class="dot"></span> 待命</span>
    </div>
    <div class="card scan-wrap" id="model_monitor">加载中...</div>
  </div>
</div>

<div class="two-col">
  <!-- ⑧ 日报 -->
  <div>
    <div class="section-title">📅 每日报告</div>
    <div class="daily-box" id="daily">加载中...</div>
  </div>
</div>

<!-- 事件流 -->
<div class="events scan-wrap" id="events_wrap">
  <div class="section-head" style="margin:0 0 10px;">
    <h3 style="color:var(--dim);font-size:13px;">📋 实时事件流</h3>
    <span class="badge-idle" id="badge_events"><span class="dot"></span> 待命</span>
  </div>
  <div class="event-list" id="events"><div style="color:var(--dim)">加载中...</div></div>
</div>

<script>
async function refresh() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();

    // ===== 活跃度特效 =====
    const act = d.activity || {};
    const fx0 = (d.cost && d.cost.today && d.cost.today._fx) || 7.1;
    const setBadge = (id, active, textActive, textIdle) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.className = active ? 'badge-active' : 'badge-idle';
      el.innerHTML = `<span class="dot"></span> ${active ? textActive : textIdle}`;
    };
    const setCard = (id, active, cls) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.classList.remove('active', 'idle', 'active-blue', 'active-red');
      if (cls === 'red') el.classList.add(active ? 'active-red' : 'idle');
      else if (cls === 'blue') el.classList.add(active ? 'active-blue' : 'idle');
      else el.classList.add(active ? 'active' : 'idle');
    };

    // 交易监控
    setBadge('badge_trade', act.trade, '🟢 交易中', '⏸ 等待行情');
    setCard('wrap_trade', act.trade, '');
    setCard('statusbar', act.trade, '');
    // AI任务市场
    setBadge('badge_tasks', act.tasks, '⚡ 任务执行中', '💤 待命');
    setCard('task_market', act.tasks, '');
    // AI Cloud
    setBadge('badge_cloud', act.cloud, '🟢 云端在线', '🔴 云离线');
    document.querySelectorAll('#cloud .cloud-card').forEach(c => c.classList.add('active'));
    // 交易AI
    setBadge('badge_ai', act.trade_ai, '🟢 分析中', '⏸ 待命');
    setCard('trade_ai', act.trade_ai, 'blue');
    // 模型调用
    setBadge('badge_model', act.model, '🔥 正在干活', '💤 空闲');
    setCard('model_monitor', act.model, 'red');
    // 事件流
    setBadge('badge_events', act.events, '📡 有活动', '🔇 安静');
    setCard('events_wrap', act.events, '');
    // 顶部实时灯
    document.getElementById('live_txt').textContent = act.model ? '🔥 AI工作中' : (act.trade ? '交易中' : '实时');

    // ① 交易
    document.getElementById('price').textContent = d.price ? '$' + d.price : '—';
    const okx = d.okx_balance;
    if (okx && okx.total_usd) {
      document.getElementById('pos').textContent = '$' + okx.total_usd.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
      document.getElementById('pos_cny').textContent = '¥' + (okx.total_usd * fx0).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0});
    } else {
      document.getElementById('pos').textContent = d.position_usdt ? '$' + d.position_usdt.toFixed(2) : '—';
      document.getElementById('pos_cny').textContent = '网格挂单值';
    }
    document.getElementById('orders').textContent = d.orders.total;
    document.getElementById('buy').textContent = (d.orders.buy > 0 || d.orders.sell > 0) ? d.orders.buy : '—';
    document.getElementById('sell').textContent = (d.orders.buy > 0 || d.orders.sell > 0) ? d.orders.sell : '—';
    document.getElementById('profit').textContent = d.profit ? (d.profit>0?'+':'') + d.profit.toFixed(2) : '—';
    const pEl = document.getElementById('profit');
    pEl.className = 'value ' + (d.profit > 0 ? 'green' : d.profit < 0 ? 'red' : '');
    document.getElementById('status').textContent = d.grid_status || '未知';
    document.getElementById('upd').textContent = '更新于 ' + (d.last_update || '—');
    document.getElementById('heartbeat').textContent = '心跳 ' + new Date().toLocaleTimeString();

    // ② 任务市场
    const tm = d.task_market.map(t => `
      <div class="task-row">
        <span class="task-name">${t.name}</span>
        <span class="task-stars">${'★'.repeat(t.stars)}${'☆'.repeat(5-t.stars)}</span>
        <span class="task-badge badge-${t.stars}">${t.stars}星</span>
        <span class="task-meta">${t.agent} · ${t.model}</span>
      </div>`).join('');
    document.getElementById('task_market').innerHTML = tm;

    // ③ 模型调度
    const dp = d.dispatch.map(x => `
      <tr>
        <td>${x.task}</td><td>${x.local}</td><td>${x.local_speed}</td>
        <td>${x.cloud}</td><td>${x.cloud_speed}</td>
        <td class="choice">${x.choice}</td>
      </tr>`).join('');
    document.getElementById('dispatch').innerHTML = `
      <table class="dispatch-table">
        <tr><th>任务</th><th>本地</th><th>速度</th><th>云</th><th>速度</th><th>选择</th></tr>
        ${dp}
      </table>`;

    // ④ AI Cloud
    const cl = d.cloud.map(c => `
      <div class="cloud-card">
        <div class="name">${c.icon} ${c.name}</div>
        <div class="region">${c.region} · ${c.role}</div>
        <div class="status">${c.status}</div>
      </div>`).join('');
    document.getElementById('cloud').innerHTML = cl;

    // ⑤ 成本 (人民币显示)
    const ct = d.cost.today;
    const fx = ct._fx || 7.1;
    const cny = usd => '¥' + (usd * fx).toFixed(2);
    const cnyDirect = v => '¥' + Number(v).toFixed(2);
    const costHtml = `
      <div class="cost-item"><div class="v green">${cny(ct.openrouter)}</div><div class="l">OpenRouter</div></div>
      <div class="cost-item"><div class="v green">${cny(ct.ollama)}</div><div class="l">Ollama</div></div>
      <div class="cost-item"><div class="v red">${cnyDirect(ct.deepseek)}</div><div class="l">DeepSeek 消费</div></div>
      <div class="cost-item"><div class="v green">${cny(ct.server)}</div><div class="l">服务器</div></div>
      <div class="cost-item"><div class="v blue">${cnyDirect(ct.deepseek)}</div><div class="l">AI 总消费</div></div>`;
    document.getElementById('cost').innerHTML = costHtml;

    // ⑥ 项目
    const pr = d.projects.map(p => `
      <div class="project-row">
        <span>${p.icon}</span><span class="project-name">${p.name}</span>
        <span class="project-status st-${p.cls}">${p.status}</span>
      </div>`).join('');
    document.getElementById('projects').innerHTML = pr;

    // ⑦ 交易AI
    const ta = d.trade_ai;
    document.getElementById('trade_ai').innerHTML = `
      <div style="font-size:13px;line-height:2.2">
        <div>📊 标的: <b>${ta.symbol}</b> &nbsp;|&nbsp; 趋势: <span class="green">${ta.trend}</span></div>
        <div>⚠️ 风险: <span class="yellow">${ta.risk}</span> &nbsp;|&nbsp; 建议: <b class="blue">${ta.advice}</b></div>
        <div style="color:var(--dim);font-size:11px">${ta.note}</div>
      </div>`;

    // ⑧ 日报
    const dl = d.daily;
    document.getElementById('daily').innerHTML = `
      <div>📅 日期: <b>${dl.date}</b></div>
      <div class="done">✅ 完成: ${dl.done.join(' / ')}</div>
      <div>🔄 运行: ${dl.running}</div>
      <div>💰 成本: <b>$${dl.cost}</b></div>
      <div>💡 建议: <span class="blue">${dl.suggestion}</span></div>`;

    // ⑨ 模型调用监控
    const ms = d.model_stats;
    const lastM = ms.last ? ms.last : {model: '—', provider: '—', in: 0, out: 0, time: ''};
    const cost = ms.cost || {deepseek: 0, openrouter: 0, local: 0, total: 0};
    const tokens = ms.tokens || {in: 0, out: 0, total: 0};
    const fx2 = ct._fx || 7.1;
    const cnyCost = usd => '¥' + (usd * fx2).toFixed(usd >= 0.01 ? 2 : 4);
    const providerBars = Object.entries(ms.by_provider || {}).map(([p, n]) => {
      const pct = ms.calls ? Math.round(n / ms.calls * 100) : 0;
      const color = p.includes('deepseek') ? 'var(--red)' : p.includes('openrouter') ? 'var(--blue)' : 'var(--green)';
      return `<div style="margin:6px 0">
        <div style="display:flex;justify-content:space-between;font-size:12px">
          <span>${p}</span><span>${n}次 (${pct}%)</span>
        </div>
        <div style="height:5px;background:#1e293b;border-radius:3px;margin-top:3px">
          <div style="width:${pct}%;height:100%;background:${color};border-radius:3px"></div>
        </div>
      </div>`;
    }).join('');
    const modelList = Object.entries(ms.by_model || {}).slice(0, 5).map(([m, n]) =>
      `<div style="font-size:12px;color:var(--dim)">${m} — ${n}次</div>`).join('') || '<div style="color:var(--dim)">暂无</div>';
    document.getElementById('model_monitor').innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <div style="font-size:13px;color:var(--dim)">当前调用</div>
        <div style="font-size:11px;color:var(--dim)">${lastM.time}</div>
      </div>
      <div style="font-size:18px;font-weight:700;color:var(--purple);margin-bottom:2px" title="${lastM.model}">${lastM.model}</div>
      <div style="font-size:12px;color:var(--dim);margin-bottom:10px">provider: ${lastM.provider} | in ${lastM.in.toLocaleString()} / out ${lastM.out.toLocaleString()} tokens</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px">
        <div style="background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.25);border-radius:8px;padding:8px;text-align:center">
          <div style="font-size:16px;font-weight:700;color:var(--red)" id="ds_used">—</div>
          <div style="font-size:10px;color:var(--dim)">DeepSeek 已用</div>
        </div>
        <div style="background:rgba(14,165,233,.08);border:1px solid rgba(14,165,233,.25);border-radius:8px;padding:8px;text-align:center">
          <div style="font-size:16px;font-weight:700;color:var(--blue)" id="ds_avail">—</div>
          <div style="font-size:10px;color:var(--dim)">DeepSeek 可用</div>
        </div>
        <div style="background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.25);border-radius:8px;padding:8px;text-align:center">
          <div style="font-size:16px;font-weight:700;color:var(--green)" id="okx_bal">—</div>
          <div style="font-size:10px;color:var(--dim)">OKX 账户</div>
        </div>
      </div>
      <div style="font-size:11px;color:var(--dim);margin-bottom:10px">📊 累计 ${ms.calls} 次调用 | ${tokens.total.toLocaleString()} tokens (in ${tokens.in.toLocaleString()} / out ${tokens.out.toLocaleString()}) · 汇率 ¥${fx2}/$</div>
      <div style="border-top:1px solid var(--border);padding-top:10px;margin-bottom:8px">
        <div style="font-size:12px;color:var(--dim);margin-bottom:4px">Provider 分布 (累计 ${ms.calls} 次)</div>
        ${providerBars}
      </div>
      <div style="border-top:1px solid var(--border);padding-top:8px">
        <div style="font-size:12px;color:var(--dim);margin-bottom:4px">模型统计</div>
        ${modelList}
      </div>`;

    // 填充真实账户数据 (DeepSeek / OKX)
    const dsb = d.ds_balance;
    document.getElementById('ds_used').textContent = dsb ? '¥' + dsb.used.toFixed(2) : '—';
    document.getElementById('ds_avail').textContent = dsb ? '¥' + dsb.available.toFixed(2) : '—';
    const okxb = d.okx_balance;
    document.getElementById('okx_bal').textContent = okxb ? '$' + okxb.total_usd.toLocaleString(undefined, {maximumFractionDigits: 0}) : '—';

    // 事件流
    if (d.events && d.events.length) {
      const evHtml = d.events.slice().reverse().map(ev => {
        const isErr = ev.includes('ERROR') || ev.includes('异常') || ev.includes('失败');
        const m = ev.match(/(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})\\s+\\[\\w+\\]\\s+(.*)/);
        const t = m ? m[1].slice(11) : '';
        const msg = m ? m[2] : ev;
        return `<div class="ev"><span class="t">${t}</span><span class="m ${isErr?'err':''}">${msg}</span></div>`;
      }).join('');
      document.getElementById('events').innerHTML = evHtml;
    }
  } catch(e) {
    document.getElementById('heartbeat').textContent = '连接错误: ' + e.message;
  }
}
refresh();
setInterval(refresh, {{ REFRESH_MS }});
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML, REFRESH_MS=REFRESH_MS)


@app.route("/api/debug")
def api_debug():
    """调试: 显示模型解析内部状态"""
    import os
    info = {
        "model_stats_file": str(MODEL_STATS_FILE),
        "exists": MODEL_STATS_FILE.exists(),
        "readable": os.access(str(MODEL_STATS_FILE), os.R_OK),
        "size": MODEL_STATS_FILE.stat().st_size if MODEL_STATS_FILE.exists() else None,
        "cache_model_stats_keys": list(_cache.get("model_stats", {}).keys()) if isinstance(_cache.get("model_stats"), dict) else type(_cache.get("model_stats")).__name__,
        "cache_model_time": _cache.get("model_cache_time"),
    }
    # 强制重解析
    _cache["model_cache_time"] = 0
    _cache["model_stats"] = {}
    stats = parse_agent_log()
    info["reparse_calls"] = stats["calls"]
    info["reparse_deepseek"] = stats["deepseek"]
    return jsonify(info)


@app.route("/api/status")
def api_status():
    parse_log()
    cloud = probe_cloud()
    model_stats = parse_agent_log()

    # 动态成本: DeepSeek 用平台真实消费 (人民币), 其他从累计统计
    fx = get_usd_cny()
    cost_today = dict(COST_CENTER["today"])
    ms_cost = model_stats.get("cost", {})
    dsb = get_deepseek_balance()
    cost_today["deepseek"] = round(dsb.get("used", 0.0), 2) if dsb and dsb.get("used") is not None else round(ms_cost.get("deepseek", 0.0), 2)
    cost_today["openrouter"] = round(ms_cost.get("openrouter", 0.0), 4)
    cost_today["ollama"] = round(ms_cost.get("local", 0.0), 4)
    cost_today["server"] = 0.0
    cost_today["_fx"] = fx  # 汇率供前端换算
    cost_today["_deepseek_cny"] = True  # deepseek 已是人民币, 前端勿再乘汇率

    # ===== 活跃度计算: 判断每个模块"正在干活" =====
    now_ts = time.time()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def parse_ts(s):
        try:
            return time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))
        except Exception:
            return 0

    # 交易监控活跃: last_update 距今 < 3 分钟
    trade_active = bool(_cache["last_update"]) and (now_ts - parse_ts(_cache["last_update"]) < 180)
    # 模型调用活跃: 最近一次模型调用 < 3 分钟
    last_model = (model_stats.get("last") or {}).get("time", "")
    model_active = bool(last_model) and (now_ts - parse_ts(last_model) < 180)
    # AI Cloud 活跃: 任一探测成功
    cloud_active = any(v.startswith("🟢") for v in cloud.values())
    # 事件流活跃: 最新事件 < 5 分钟
    events_active = False
    if _cache["events"]:
        for ev in reversed(_cache["events"]):
            m = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", ev)
            if m and (now_ts - parse_ts(m.group(1)) < 300):
                events_active = True
                break
    # 任务市场活跃: 模型正在调用则视为任务在跑
    tasks_active = model_active
    # 交易AI活跃: 跟随交易
    trade_ai_active = trade_active

    activity = {
        "trade": trade_active,
        "model": model_active,
        "cloud": cloud_active,
        "events": events_active,
        "tasks": tasks_active,
        "trade_ai": trade_ai_active,
        "now": now_str,
    }

    # OKX / DeepSeek 真实账户 (带缓存)
    okx = get_okx_balance()
    ds_bal = get_deepseek_balance()

    return jsonify({
        "price": _cache["price"],
        "position_usdt": round(_cache["position_usdt"], 2),
        "okx_balance": okx,   # 真实账户总估值 (USD)
        "ds_balance": ds_bal, # DeepSeek 真实余额 (元)
        "orders": _cache["orders"],
        "grid_status": _cache["grid_status"],
        "last_update": _cache["last_update"],
        "profit": round(_cache["profit"], 2),
        "events": list(_cache["events"]),
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "activity": activity,
        # 模型调用统计 (新增)
        "model_stats": {
            "calls": model_stats["calls"],
            "by_provider": model_stats["by_provider"],
            "by_model": model_stats["by_model"],
            "last": model_stats["last"],
            "deepseek": model_stats["deepseek"],
            "tokens": model_stats.get("tokens", {"in": 0, "out": 0, "total": 0}),
            "cost": model_stats.get("cost", {"deepseek": 0.0, "openrouter": 0.0, "local": 0.0, "total": 0.0}),
        },
        # 配置数据
        "task_market": [{"name": k, "stars": v["stars"], "agent": v["agent"], "model": v["model"]}
                        for k, v in TASK_MARKET.items()],
        "dispatch": MODEL_DISPATCH,
        "cloud": [{"name": c["name"], "region": c["region"], "role": c["role"], "icon": c["icon"],
                   "status": {"openrouter": cloud.get("openrouter", "—"),
                              "nvidia": "🟢 可用",
                              "deepseek": cloud.get("deepseek", "—"),
                              "ollama": cloud.get("ollama", "—")}.get(
                       {"OpenRouter": "openrouter", "NVIDIA Cloud": "nvidia",
                        "DeepSeek": "deepseek", "Local Ollama": "ollama"}[c["name"]], "—")}
                  for c in AI_CLOUD],
        "cost": {"today": cost_today, "monthly": COST_CENTER["monthly"]},
        "projects": [{"name": p["name"], "status": p["status"], "icon": p["icon"],
                      "cls": {"开发中": "dev", "开发": "dev", "MVP": "mvp", "规划": "plan"}.get(p["status"], "plan")}
                     for p in PROJECTS],
        "trade_ai": TRADE_AI,
        "daily": DAILY_REPORT,
    })


if __name__ == "__main__":
    print("=" * 55)
    print("🎯 Hermes AI OS 综合监控大屏 V2 启动")
    print(f"  日志: {LOG_FILE}")
    print(f"  本机: http://127.0.0.1:{PORT}")
    print(f"  局域网: http://<本机IP>:{PORT}")
    print("=" * 55)
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
