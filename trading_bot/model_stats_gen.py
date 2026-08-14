#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型调用统计生成器 (增量累计模式)
由 Hermes cron 定时运行 (Hermes 进程有权读 ~/.hermes/logs/)
- 增量解析 agent.log: 每次只读上次位置之后的新增行
- 累计统计: 所有 provider 的 token 消耗 + 金额
- 写入 ~/leo-ai-os/trading_bot/model_stats.json (dashboard 可读)
"""
import re
import json
import time
from pathlib import Path

AGENT_LOG = Path.home() / ".hermes" / "logs" / "agent.log"
OUT_FILE = Path.home() / "leo-ai-os" / "trading_bot" / "model_stats.json"
STATE_FILE = Path.home() / "leo-ai-os" / "trading_bot" / ".model_stats_pos"

# ===== 定价 (人民币/M tokens) — DeepSeek 官方 2026-08-06 =====
DS_PRICE_IN_MISS = 1.0     # 缓存未命中输入 (元/M)
DS_PRICE_IN_HIT = 0.02     # 缓存命中输入 (元/M)
DS_PRICE_OUT = 2.0         # 输出 (元/M)

# OpenRouter 主流模型参考价 ($/M) — 免费模型为 0
OR_PRICES = {
    "nvidia/nemotron-3-ultra-550b-a55b:free": (0.0, 0.0),
    "openrouter/free": (0.0, 0.0),
    "nvidia/nemotron-nano-12b-v2-vl:free": (0.0, 0.0),
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": (0.0, 0.0),
    "deepseek/deepseek-chat-v3.1": (0.28, 0.42),
    "deepseek/deepseek-r1": (0.55, 2.19),
    "anthropic/claude-sonnet-4": (3.0, 15.0),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "meta-llama/llama-3.3-70b-instruct:free": (0.0, 0.0),
    "qwen/qwen3-235b-a22b:free": (0.0, 0.0),
}

# Ollama 本地模型: 0 成本
LOCAL_PROVIDERS = {"ollama", "custom", "local"}


def load_state():
    try:
        return int(STATE_FILE.read_text().strip())
    except Exception:
        return 0


def save_state(pos):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(str(pos))
    except Exception:
        pass


def load_prev_stats():
    try:
        return json.loads(OUT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def cost_for(provider, model, tin, tout, cache_hit=0.0):
    """计算一次调用的成本 (返回人民币元)

    cache_hit: 0~1, 本次调用输入中缓存命中的比例
    """
    if provider == "deepseek":
        cost_in = (tin * cache_hit * DS_PRICE_IN_HIT +
                   tin * (1 - cache_hit) * DS_PRICE_IN_MISS) / 1e6
        cost_out = tout * DS_PRICE_OUT / 1e6
        return cost_in + cost_out
    if provider in LOCAL_PROVIDERS:
        return 0.0
    # OpenRouter: 查参考价 (USD), 免费模型为 0; 非免费按 7.1 汇率换算人民币
    p_in, p_out = OR_PRICES.get(model, (0.0, 0.0))
    if p_in == 0 and p_out == 0:
        return 0.0
    return (tin * p_in + tout * p_out) / 1e6 * 7.1


def new_stats():
    return {
        "calls": 0,
        "by_provider": {},
        "by_model": {},
        "tokens": {"in": 0, "out": 0, "total": 0},
        "cost": {"deepseek": 0.0, "openrouter": 0.0, "local": 0.0, "total": 0.0},
        "last": None,
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def merge(prev, fresh):
    """合并累计统计与本次增量"""
    if not prev:
        return fresh

    prev["calls"] += fresh["calls"]
    for p, n in fresh["by_provider"].items():
        prev["by_provider"][p] = prev["by_provider"].get(p, 0) + n
    for m, n in fresh["by_model"].items():
        prev["by_model"][m] = prev["by_model"].get(m, 0) + n
    for k in ("in", "out", "total"):
        prev["tokens"][k] += fresh["tokens"][k]
    for k in ("deepseek", "openrouter", "local", "total"):
        prev["cost"][k] = round(prev["cost"].get(k, 0.0) + fresh["cost"][k], 6)
    if fresh["last"]:
        prev["last"] = fresh["last"]
    prev["generated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return prev


def parse_increment():
    """增量读取: 从上次位置读新增行"""
    fresh = new_stats()
    last_pos = load_state()

    try:
        with open(AGENT_LOG, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)
            size = f.tell()
            # 文件被轮转/清空 (大小 < 上次位置): 从头读
            if size < last_pos:
                last_pos = 0
            f.seek(last_pos)
            new_lines = f.readlines()
            new_pos = f.tell()
    except Exception as e:
        fresh["error"] = str(e)
        return fresh, None

    for line in new_lines:
        m = re.search(r"API call #\d+: model=(\S+) provider=(\S+) in=(\d+) out=(\d+) total=(\d+)", line)
        if not m:
            continue
        model, provider = m.group(1), m.group(2)
        tin, tout = int(m.group(3)), int(m.group(4))

        # 提取真实缓存命中率 (cache=命中/总量)
        cache_hit = 0.0
        cm = re.search(r"cache=(\d+)/(\d+)", line)
        if cm:
            total = int(cm.group(2))
            if total > 0:
                cache_hit = int(cm.group(1)) / total

        fresh["calls"] += 1
        fresh["by_provider"][provider] = fresh["by_provider"].get(provider, 0) + 1
        fresh["by_model"][model] = fresh["by_model"].get(model, 0) + 1
        fresh["tokens"]["in"] += tin
        fresh["tokens"]["out"] += tout
        fresh["tokens"]["total"] += tin + tout

        c = cost_for(provider, model, tin, tout, cache_hit)
        if provider == "deepseek":
            fresh["cost"]["deepseek"] += c
        elif provider in LOCAL_PROVIDERS:
            fresh["cost"]["local"] += c
        else:
            fresh["cost"]["openrouter"] += c
        fresh["cost"]["total"] += c

        t = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        fresh["last"] = {"model": model, "provider": provider,
                         "in": tin, "out": tout, "cost": round(c, 6),
                         "time": t.group(1) if t else ""}

    # 四舍五入到 4 位
    for k in ("deepseek", "openrouter", "local", "total"):
        fresh["cost"][k] = round(fresh["cost"][k], 4)

    return fresh, new_pos


if __name__ == "__main__":
    fresh, new_pos = parse_increment()
    prev = load_prev_stats()

    # 若文件被轮转 (prev 存在但本轮 error), 保留 prev 只更新 last
    if fresh.get("error") and prev:
        prev["generated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        data = prev
    else:
        data = merge(prev, fresh)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if new_pos is not None:
        save_state(new_pos)

    c = data["cost"]
    print(f"✅ 累计: {data['calls']} calls | tokens {data['tokens']['total']:,} | "
          f"DS ${c['deepseek']:.4f} + OR ${c['openrouter']:.4f} + 本地 ${c['local']:.4f} = ${c['total']:.4f}")
