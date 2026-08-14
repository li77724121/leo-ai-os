# TELEGRAM CEO DISPATCHER — Hermes 调度中枢接线说明

> 版本：V1.1（第一层 CEObot ↔ Hermes 已接通 + 消息 7 级分级）
> 定位：把 Telegram 群「hermes公司」从"聊天群"变成"一人 AI 公司指挥中心"
> 上级文档：`COMPANY_ARCHITECTURE_V2.md`（自主闭环架构 V2.0）、`AI_EMPLOYEE_ROSTER.md`（52 角色花名册）

---

## 0. 一句话架构

> **Leo 只对 CEObot 下命令；Hermes 是唯一 CEO/Orchestrator（单一大脑）；部门 Bot 是名片；Worker 设备负责执行。禁止 Bot 之间互相聊天（会死循环）；禁止把"回复消息"当成"完成工作"。**

```
👤 Lee Leo（创始人：想法/方向/审批）
        │  一句话/一个命令
        ▼
📱 Telegram 群「hermes公司」
        │
        ▼
🤖 CEObot (@CEOleo_bot) ── 唯一接后端
        │
        ▼
🧠 Hermes CEO / Orchestrator（MacBook MASTER，唯一大脑）
        │  六步流程 → 任务拆解 → 部门分派
        ├── 战略部 / 产品部 / 工程部 / 运维部 / 运营部 / 财务部 / 风控部
        │        （= Hermes 内部技能/角色分派，非独立 Bot）
        ▼
🖥 Worker 设备：Mac mini（工程/OpenClaw） + 极空间 NAS（数据/备份）
```

---

## 1. 群成员定位表（8 成员）

| 群成员 | 角色 | 后端接线 | 职责 |
|---|---|---|---|
| **CEObot** (@CEOleo_bot) | CEO / 总调度 | ✅ **唯一接 Hermes 后端** | 接收 Leo 命令 → 六步流程 → 分派部门 → 汇报结果 |
| **Lee Leo** | 创始人 | 人工 | 想法 / 方向 / 重大决策 / 最终审批 |
| Product Manager | 产品部 | 名片（无后端） | 由 Hermes 代表：PRD / 竞品 / 路线图 |
| Marketing Manager | 营销部 | 名片（无后端） | 由 Hermes 代表：内容 / 推广 / 引流 |
| PowerPM Engineer | 工程部（新能源） | 名片（无后端） | 由 Hermes 代表：施工方案 / 报价 / 风险分析 |
| CFO Finance | 财务部 | 名片（无后端） | 由 Hermes 代表：成本 / 收入 / 现金流 |
| 1bot | 通用 Worker | 名片（极空间） | NAS 执行节点，按 Hermes 指令跑任务 |
| 大龙虾 | 自动化 Worker | 名片（OpenClaw） | Mac mini 的 OpenClaw 自动化节点 |

> **关键**：只有 CEObot 接 Hermes 后端。其余 7 个成员**不需要各自跑模型**——Hermes 是"唯一大脑"，部门 Agent 是 Hermes 内部的技能/角色分派，不是独立 Bot。这从根上杜绝"8 个机器人互相乱聊"的死循环风险。

---

## 2. 命令路由（自然语言 → 部门分派）

Hermes 收到 Leo 的命令后，按**语义**路由到对应部门（对齐 `COMPANY_ARCHITECTURE_V2.md` 六部门）：

| 输入关键词/意图 | 路由部门 | 主要技能包 |
|---|---|---|
| 战略 / 商业 / 机会 / 方向 / 竞品 / 定价 | 战略部 | nuwa-skill、elon-musk-perspective、gbrain |
| 产品 / PRD / 需求 / 用户 / 原型 | 产品部 | pm-skills（pm-product-discovery / pm-product-strategy） |
| 开发 / 代码 / Bug / 测试 / 架构 | 工程部 | superpowers、addyosmani agent-skills、trailofbits（风控） |
| 营销 / 增长 / 内容 / 引流 / 发布 | 运营部 | wigolo、dbskill、MoneyPrinterTurbo |
| 财务 / 成本 / 收入 / 现金流 / 交易 | 财务部 | gmgn-skills、onchainos、agent-trade-kit（默认纸面模式） |
| 新能源 / 充电桩 / 换电站 / 工程方案 / 报价 | 工程部（PowerPM） | PowerPM AI 助手 |
| 自动化 / 运维 / 部署 / 自愈 | 运维部 | SRE_Agent、hermes-agent、selfheal |
| 安全 / 漏洞 / 审计 | 风控部 | trailofbits（semgrep / codeql / supply-chain 等） |

---

## 3. Telegram 命令集

| 命令 | 作用 | 路由 |
|---|---|---|
| `/ceo` | 显示调度中枢状态 + 当前任务队列 | CEO |
| `/plan <想法>` | 把想法转成六步执行计划 | CEO / 战略部 |
| `/research <主题>` | 深度调研并出报告 | 战略部 / 运营部 |
| `/product <需求>` | 生成 PRD / 产品方案 | 产品部 |
| `/code <任务>` | 开发 / 写码 | 工程部 |
| `/test` | 跑测试 / QA | 工程部 |
| `/marketing <产品>` | 内容 / 推广方案 | 运营部 |
| `/finance` | 成本 / 收入 / 现金流 | 财务部 |
| `/powerpm <项目>` | 新能源工程方案 / 报价 / 风险 | 工程部（PowerPM） |
| `/status` | 查看任务/项目/设备状态 | CEO / 运维部 |
| `/release` | 发布流程检查 | 运营部 / 工程部 |
| `/memory` | 读写公司知识库 | CEO |
| `/health` | 三节点健康检查 | 运维部 |
| `/help` | 帮助 | CEO |

> 以上命令是快捷入口，**自然语言同样有效**。Leo 说"做一个免费的 Mac 图片压缩工具"与 `/product 图片压缩工具` 等价。

---

## 4. Task ID 规范

所有持久任务生成唯一 ID：

```
LEO-YYYYMMDD-XXXX
```

示例：`LEO-20260814-0001`

文件、日志、Git 提交、报告、产物尽可能关联 Task ID，便于跨设备 / 跨会话恢复。

---

## 5. 报告格式（新规范，取代 SOUL.md 第十章旧格式）

> 旧格式（已废弃）：【任务】【商业价值】【执行计划】【调用Agent】【预计结果】【风险】
> **新格式**：

```
【TASK】    LEO-YYYYMMDD-XXXX
【任务】    一句话任务目标
【负责人】  部门 / Agent / 设备
【设备】    MacBook / Mac mini / NAS
【状态】    PENDING / RUNNING / BLOCKED / DONE / FAILED
【结果】    真实执行结果（非承诺）
【产物】    文件路径 / URL / Git commit / 测试结果
【成本】    token / 时间 / 现金
【下一步】  明确的后续动作
```

**铁律**：`DONE` 必须有 Proof of Work（真实文件/URL/Git 提交/测试日志），禁止无证据声称完成。

---

## 6. 消息分级处理（7 级）

Leo 的每条消息先按**风险分级**，再决定「处理策略」与「是否需要确认」。从低到高：

| 级别 | 类型 | 示例 | 处理策略 | Leo 确认 |
|---|---|---|---|---|
| **L1** | 普通聊天 | "早上好" / 闲聊 | AI 直接友好回复，零成本，不建 Task | 否 |
| **L2** | 信息查询 | "PowerPM 是什么" / 查资料 | 检索知识库后回复，不建 Task | 否 |
| **L3** | 任务命令 | "查下 BTC 价格" / 单次任务 | 拆解 → 执行 → 汇报（先执行后汇报） | 否 |
| **L4** | 项目命令 | "做 PowerPM 报价功能" | 六步流程 → 分派 Agent → 生成 Task ID，里程碑汇报 | 否 |
| **L5** | 实时业务查询 | "抄币赚了多少" / 设备在线 | 只读查真实数据，数据必须真实 | 否 |
| **L6** | 赚钱 / 现金流查询 | "账户余额 / 收入成本" | 只读查账，口径 = 落袋为安（浮盈不算） | 否 |
| **L7** | 高风险操作 | "买入 BTC" / 删文件 / 系统权限 / 账号密码 | 🔴 先汇报方案，等确认后才执行 | **是** |

**铁律**：
- L1–L6 = 低风险 → **先执行后汇报**；L7 = 高影响 → **先汇报后执行**。
- L5 / L6 是只读，但**数据必须真实**，禁止编造浮盈 / 收入。
- L7 涉及资金 / 删除 / 权限 / 密码 → **绝不自动执行**，未确认前只出方案不动手。
- 内容发布到第三方平台、对外签约、重大法律 / 商业承诺 → 归 L7 前置（先过目再发）。
- 不确定属于哪一级 → 按更高级别处理（宁可多确认一次，不可越权）。

---

## 7. 故障转移

- **单个 Agent 失败** → 重试 3 次 → 分析原因 → 换工具/换模型/换节点 → 仍失败标记 `BLOCKED` 并上报 CEO。
- **单节点离线**（如 Mac mini 离线）→ MacBook 继续；NAS 离线 → MacBook + mini 继续；全部离线 → NAS 保留 Task Queue / Memory / 产物，恢复后自动 Resume。
- **模型失败** → 按 `MODEL_ROUTING.md` 切换备用免费模型。
- **禁止死循环** → 每个 Task 设最大重试次数 / 最大执行时间 / 最大 token 预算，超限触发熔断（Circuit Breaker）。

---

## 8. 优先级

```
P0 系统故障  >  P1 收入  >  P2 真实用户  >  P3 正在开发产品  >  P4 营销/实验
```

即：现金流 → 用户 → 产品 → 系统 → 实验。可自动降低长期无用户/无收入/无增长项目的优先级（进入 ARCHIVED，不删除核心资产）。

---

## 9. 第一层接线状态（CEObot ↔ Hermes）

**已接通**，靠 Hermes gateway 配置实现（无需额外代码）：

| 配置项 | 值 | 说明 |
|---|---|---|
| `telegram.proxy_url` | `http://127.0.0.1:7897` | Clash Verge 代理（Telegram 直连超时，必须走代理） |
| `telegram.group_allowed_chats` | `<群ID>` | 群「hermes公司」supergroup id（真实值见本地 config.yaml） |
| `telegram.group_allow_from` | `<你的用户ID>` | 只接受 Leo 的指令（真实值见本地 config.yaml） |
| `telegram.observe_unmentioned_group_messages` | `true` | 群里消息（即使不 @bot）也交给 Hermes 观察处理 |
| `model.default` | `nvidia/nemotron-3-nano-30b-a3b:free` | 免费模型，实测无 429、支持工具调用 |

> 即：Leo 在群里随便说一句话，CEObot（= Hermes gateway）就会收到并处理。这是第一层，已经跑通。

---

## 10. 后续接线路线图

| 阶段 | 内容 | 状态 |
|---|---|---|
| **第一层** | CEObot ↔ Hermes（唯一大脑） | ✅ 已接通 |
| 第二层 | 部门 Agent 逐个接入（先 PowerPM，再 Product/Marketing/CFO） | ⏳ 待接 |
| 第三层 | Worker 设备执行（Mac mini OpenClaw + 极空间 NAS 任务下发） | ⏳ 待接（Mac mini 需开机） |

**第一层原则**：先只把 CEObot 和 Hermes 跑通（= 本阶段目标），其余部门 Bot 保持"名片"状态，逐个接入、逐个验证，避免一次接太多导致互相干扰。
