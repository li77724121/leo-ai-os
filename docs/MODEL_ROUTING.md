# 模型路由策略 MODEL ROUTING（V1 · 实测校准版）

> 原则：**按岗位分工用模型团队，不靠一个大模型包打天下。**
> 本表全部基于 2026-08-14 14:20 双连发实测（1 次成功不代表可用，需 2 连发无 429 才算稳）。

## 实测结论（真实数据，勿凭参数臆断）

| 模型 | 实测 | 判定 | Hermes 岗位 |
|---|---|---|---|
| `nvidia/nemotron-3-nano-30b-a3b:free` | 1.0s / 0.8s OK | ✅ 稳定 | 🥇 **主循环默认**（快、支持工具、无 429） |
| `nvidia/nemotron-3.5-lightning:free` | 0.7s / 1.2s OK | ✅ 快 | ⚡ 快速主力/备用 |
| `nvidia/nemotron-3-super-120b-a12b:free` | 1.9s / 1.4s OK | ✅ 快 | 🧠 **复杂推理/子Agent**（delegation） |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | 1.1s OK / 1.0s **502** | ⚠️ 不稳 | 仅异步离线+重试，不挂实时链路 |
| `google/gemma-4-26b-a4b-it:free` | 1.4s / 7.3s OK | ⚠️ 波动 | 备用（延迟飘，7s+） |
| `openai/gpt-oss-20b:free` | 7.1s / **429** | ⚠️ 限流 | 备用（2 连发第 2 次 429） |
| `google/gemma-4-31b-it:free` | **429 / 429** | ❌ 已死 | 移除 |
| `liquid/lfm-2.5-2.6b:free` | 空内容 | ❌ 已死 | 移除 |

## 六层模型池（校准后）

```
第一层 GENERAL FAST（实时主链路，必须无 429）
  ├── Nemotron Nano 30B   ← 默认主循环（Hermes default）
  ├── Nemotron Lightning  ← 快速备用
  └── Nemotron Super 120B ← 复杂任务 / 子Agent（Hermes delegation）

第二层 FALLBACK（异步离线可用，带重试）
  ├── Nemotron Ultra 550B（502/排队，仅离线重试）
  ├── Gemma 26B（延迟波动）
  └── GPT-OSS 20B（限流）

第三层 CODING FREE（走 CLI，不经 OpenRouter 主循环）
  └── Laguna S / XS / North Mini Code → 由 opencode / codex 子Agent 调用

第四层 VISION
  ├── 本地 ollama/llava:7b（Mac mini，已配，无工具调用）
  └── Nemotron Omni / Nano VL（云端，待实测后再纳入）

第五层 COMPANY MEMORY（极空间 NAS）
  └── Embed VL + Rerank VL（记忆/检索，非对话模型）

第六层 ESCALATION（免费池解决不了 / 重大决策）
  └── DeepSeek（compression 已用 deepseek-v4-flash；重大复核用 deepseek 主模型）
```

## Hermes 实际配置（已落地）

| 项 | 值 |
|---|---|
| `model.default` | `nvidia/nemotron-3-nano-30b-a3b:free`（主循环） |
| `delegation.model` | `nvidia/nemotron-3-super-120b-a12b:free`（复杂子任务） |
| `delegation.provider` | `openrouter` |
| `model.vision_provider` | `ollama/llava:7b`（本地 mini） |
| `auxiliary.compression` | `deepseek/deepseek-v4-flash`（长对话压缩） |

## 路由规则

```
普通聊天 / 信息查询 / 日常任务 → Nano 30B（默认主循环）
复杂推理 / 规划 / 拆解 / 多Agent → Super 120B（delegation 子Agent）
Coding                          → opencode / codex CLI（Laguna/North）
Vision                           → 本地 llava:7b（mini）
记忆 / 检索                       → 极空间 Embed + Rerank
无法判断                         → 默认 Nano（OpenRouter/free 路由已弃，直接指定更稳）
免费模型解决不了 / 重大决策        → DeepSeek 复核，涉资金风险再经 Leo 批准
```

## 动态模型发现（免费模型不永久，勿写死）

> OpenRouter 官方明确：免费模型会持续更新，但**不能保证永久免费**，且免费层有低速率限制，很多免费模型不适合生产。因此本表是「当前实测快照」，**不是永久架构**。

- **发现 → 测试 → 排名 → 自动替换**循环，不能把公司生命线绑死在某几个免费模型上。
- 纳入实时链路前必须 **2 连发无 429**（1 次成功不算数）。
- 免费模型不可靠 → 换另一个免费 → 仍不行 → DeepSeek 升级。
- 本表 `实测` 列每轮会失效，需定期重测刷新（建议每周/模型池变动时）。

## 设备分工（不变）

- **MacBook** = Hermes 主脑 + Telegram + 云端路由（不下大型模型）
- **Mac mini** = Ollama 本地模型（llava 等）+ 工程执行
- **极空间 NAS** = 记忆 / 数据 / 备份 / 灾备

## 铁律

1. 免费模型「一次成功」不算数，必须 **2 连发无 429** 才可纳入实时链路。
2. 换 provider 后未 pin 的 cron 会 fail closed，须 `hermes cron edit` 重 pin。
3. 550B/31B 这类「名字大」的免费模型常排队/限流，宁可要 30B/120B 的稳定小模型，不要 90s 排队的大模型。
