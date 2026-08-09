# 交易自动化系统架构设计

> 版本：v1.0
> 更新：2026-06-29
> 状态：设计中

---

## 1. 系统总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRADING AUTOMATION SYSTEM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  STRATEGY    │  │   RISK       │  │  EXECUTION   │          │
│  │  LAYER       │──│   LAYER      │──│  LAYER       │          │
│  │              │  │              │  │              │          │
│  │ • Grid       │  │ • Position   │  │ • OKX CLI    │          │
│  │ • DCA        │  │   Sizing     │  │   Wrapper    │          │
│  │ • Arbitrage  │  │ • Stop Loss  │  │ • Order Mgmt │          │
│  │ • Trend      │  │ • Correlation│  │ • State Sync │          │
│  │ • Factor     │  │ • Exposure   │  │ • Retry/Rec  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                     │
│              ┌────────────────────────┐                         │
│              │    DATA LAYER          │                         │
│              │                        │                         │
│              │ • Market Data (REST/WS)│                         │
│              │ • Account State        │                         │
│              │ • Historical DB        │                         │
│              │ • Strategy Params      │                         │
│              │ • Trade Logs           │                         │
│              └───────────┬────────────┘                         │
│                          │                                       │
│         ┌────────────────┼────────────────┐                     │
│         ▼                ▼                ▼                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ MONITORING │  │  REVIEW    │  │  ALERTING  │                │
│  │  DASHBOARD │  │   ENGINE   │  │  SYSTEM    │                │
│  │            │  │            │  │            │                │
│  │ • Real PnL │  │ • Daily    │  │ • Telegram │                │
│  │ • Positions│  │ • Weekly   │  │ • Email    │                │
│  │ • Greeks   │  │ • Monthly  │  │ • Webhook  │                │
│  │ • Risk     │  │ • Attribution     │                │
│  └────────────┘  └────────────┘  └────────────┘                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 五层架构详细设计

### 2.1 策略层

**职责**：策略定义、参数化、生命周期管理

```python
# 策略基类接口
class BaseStrategy:
    name: str                    # 策略唯一标识
    version: str                 # 版本号
    params: StrategyParams       # 可配置参数
    state: StrategyState         # 运行状态
    
    def on_init(self, context: Context) -> None: ...
    def on_tick(self, context: Context) -> List[Order]: ...
    def on_order_update(self, order: Order) -> None: ...
    def on_position_update(self, pos: Position) -> None: ...
    def on_stop(self, context: Context) -> None: ...
    
    def validate_params(self) -> ValidationResult: ...
    def get_required_data(self) -> List[DataRequirement]: ...
```

**策略注册表**：
```
strategies/
├── grid/
│   ├── spot_grid.py           # 现货网格
│   ├── futures_grid.py        # 合约网格
│   └── params_schema.json     # 参数 JSON Schema
├── dca/
│   ├── spot_dca.py
│   └── params_schema.json
├── arbitrage/
│   ├── funding_rate.py
│   ├── spot_futures.py
│   └── params_schema.json
├── trend/
│   ├── ma_crossover.py
│   ├── breakout.py
│   └── params_schema.json
└── registry.json              # 策略元数据索引
```

**参数化规范**（所有策略必须提供）：
```json
{
  "strategy_id": "grid_spot_v1",
  "name": "Spot Grid Trading",
  "version": "1.0.0",
  "params_schema": {
    "type": "object",
    "properties": {
      "instId": {"type": "string", "description": "交易对，如 BTC-USDT"},
      "grid_num": {"type": "integer", "minimum": 5, "maximum": 200},
      "min_price": {"type": "number", "exclusiveMinimum": 0},
      "max_price": {"type": "number", "exclusiveMinimum": 0},
      "investment": {"type": "number", "description": "投入金额(USDT)"},
      "run_type": {"type": "string", "enum": ["auto", "manual"]},
      "tp_trigger": {"type": "number", "description": "止盈触发价"},
      "sl_trigger": {"type": "number", "description": "止损触发价"}
    },
    "required": ["instId", "grid_num", "min_price", "max_price", "investment"]
  },
  "default_params": {
    "grid_num": 20,
    "run_type": "auto"
  },
  "risk_limits": {
    "max_position_pct": 0.1,
    "max_drawdown_pct": 0.15,
    "correlation_limit": 0.7
  }
}
```

---

### 2.2 风控层

**核心原则**：资金保护 > 收益最大化

| 风控模块 | 规则 | 执行方式 |
|----------|------|----------|
| **单策略仓位限制** | ≤ 总权益 10% | 下单前预检 |
| **单品种敞口限制** | ≤ 总权益 20% | 实时监控 |
| **相关性限制** | 高相关策略(>0.7)合计 ≤ 15% | 组合层面 |
| **最大回撤** | 策略级 15%，账户级 10% | 触发熔断 |
| **单笔损失** | ≤ 单策略投入 2% | 止损单 |
| **资金费率风险** | 合约策略强制监控资金费率 | 实时告警 |
| **流动性风险** | 只交易 24h 量 > $10M 的标的 | 预检过滤 |

**熔断机制**：
```
L1 告警：单策略回撤 > 8% → 仅告警，继续运行
L2 警告：单策略回撤 > 12% → 停止开新仓，仅允许平仓
L3 熔断：单策略回撤 > 15% 或 账户回撤 > 10% → 全部平仓，停止所有策略
```

---

### 2.3 执行层

**OKX CLI 封装设计**：

```python
class OKXExecutor:
    """统一执行接口，支持实盘/模拟无缝切换"""
    
    def __init__(self, profile: str = "okx-live", demo: bool = False):
        self.profile = profile
        self.demo = demo
        self._verify_auth()
    
    # === 订单管理 ===
    def place_order(self, order: Order) -> OrderResult: ...
    def cancel_order(self, instId: str, ordId: str) -> CancelResult: ...
    def amend_order(self, instId: str, ordId: str, new_px: float, new_sz: float) -> AmendResult: ...
    
    # === 策略专用 ===
    def start_grid(self, params: GridParams) -> AlgoResult: ...
    def stop_grid(self, algoId: str) -> AlgoResult: ...
    def start_dca(self, params: DCAParams) -> AlgoResult: ...
    
    # === 状态同步 ===
    def sync_positions(self) -> List[Position]: ...
    def sync_orders(self, instId: str = None) -> List[Order]: ...
    def sync_algo_orders(self) -> List[AlgoOrder]: ...
    
    # === 账户 ===
    def get_balance(self) -> AccountBalance: ...
    def get_positions(self) -> List[Position]: ...
    
    # === 重试与熔断 ===
    def _execute_with_retry(self, cmd: List[str], max_retry: int = 3) -> Result: ...
    def _check_circuit_breaker(self) -> bool: ...
```

**幂等性保证**：
- 每个订单携带 `clOrdId` (client order id) = `strategy_id + timestamp + uuid`
- 重试时复用同一 `clOrdId`，OKX 自动去重
- 状态机：`PENDING → SUBMITTED → PARTIAL/FILLED/CANCELLED/REJECTED`

---

### 2.4 数据层

**存储架构**：

```
data/
├── market/                    # 行情数据
│   ├── raw/                   # 原始 tick/kline
│   │   ├── BTC-USDT/
│   │   │   ├── 2026-06-29.tick.parquet
│   │   │   └── 2026-06-29.1m.parquet
│   │   └── ...
│   └── processed/             # 清洗后特征
│       └── features.parquet
├── account/                   # 账户状态快照
│   ├── balance_2026-06-29_00-00-00.json
│   ├── positions_2026-06-29_00-00-00.json
│   └── ...
├── trades/                    # 成交记录
│   ├── 2026-06-29_trades.parquet
│   └── ...
├── strategies/                # 策略运行日志
│   ├── grid_spot_v1/
│   │   ├── 2026-06-29.log
│   │   ├── params.json
│   │   └── state.json
│   └── ...
└── backtest/                  # 回测结果
    ├── grid_spot_v1_BTC-USDT_2026-01-01_2026-06-29/
    │   ├── report.html
    │   ├── equity_curve.parquet
    │   └── trades.parquet
    └── ...
```

**数据获取优先级**：
1. 本地缓存（优先，离线可用）
2. OKX REST API（实时、历史）
3. OKX WebSocket（实时推送）

---

### 2.5 监控/复盘/告警层

**监控看板指标**：
| 类别 | 指标 | 刷新频率 |
|------|------|----------|
| **PnL** | 总权益、未实现盈亏、已实现盈亏、日/周/月收益率 | 10s |
| **持仓** | 各策略持仓、杠杆、保证金率、资金费率 | 10s |
| **风险** | 最大回撤、夏普、卡尔马、VaR、相关性矩阵 | 1min |
| **执行** | 订单成功率、滑点、延迟、API 错误率 | 1min |
| **策略** | 网格成交数、DCA 买入均价、套利利润 | 1min |

**复盘 SOP 模板**：
```
DAILY REVIEW (每日 00:05 UTC)
├── 市场概览：BTC/ETH 涨跌、资金费率、基差
├── 策略表现：各策略 PnL、成交统计、参数偏离
├── 风险检查：敞口、回撤、相关性、异常订单
├── 执行质量：滑点、延迟、失败订单分析
└── 行动项：参数调整、停止/启动策略、风控升级

WEEKLY REVIEW (每周一 00:00 UTC)
├── 收益归因：Alpha/Beta 分解、策略贡献度
├── 参数优化：网格区间、DCA 间隔、止损位回测
├── 容量评估：策略能否加仓、新品种可行性
└── 系统健康：数据完整性、API 稳定性、存储增长

MONTHLY REVIEW (每月 1 号 00:00 UTC)
├── 组合优化：相关性调整、新策略上线评估
├── 资本分配：各策略权重再平衡
├── 基础设施：成本分析、扩容规划
└── 知识沉淀：更新 SOP、参数模板、避坑指南
```

**告警规则**：
```yaml
alerts:
  - name: "strategy_drawdown_8pct"
    condition: "strategy.drawdown_pct > 0.08"
    level: "warning"
    channels: ["telegram"]
    cooldown: "1h"
    
  - name: "account_drawdown_10pct"
    condition: "account.drawdown_pct > 0.10"
    level: "critical"
    channels: ["telegram", "email"]
    action: "circuit_break_all"
    
  - name: "api_error_rate_high"
    condition: "executor.error_rate_5min > 0.1"
    level: "warning"
    channels: ["telegram"]
    
  - name: "grid_no_trades_4h"
    condition: "grid.trades_last_4h == 0 and grid.state == 'running'"
    level: "info"
    channels: ["telegram"]
```

---

## 3. 数据流设计

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ MARKET  │────▶│ STRATEGY│────▶│  RISK   │────▶│EXECUTOR │────▶│ EXCHANGE│
│  DATA   │     │  ENGINE │     │ CHECK   │     │         │     │  (OKX)  │
└─────────┘     └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
                     │               │               │               │
                     ▼               ▼               ▼               ▼
              ┌─────────────────────────────────────────────────────────┐
              │                    STATE STORE                          │
              │  (Positions, Orders, Balances, Strategy States, Logs)  │
              └─────────────────────────────────────────────────────────┘
                     │               │               │               │
                     ▼               ▼               ▼               ▼
              ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
              │ MONITOR  │   │  REVIEW  │   │  ALERT   │   │ BACKTEST │
              │ DASHBOARD│   │  ENGINE  │   │ SYSTEM   │   │  ENGINE  │
              └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

---

## 4. 部署拓扑

```
┌────────────────────────────────────────────────────────────┐
│                    MAC MINI M1 (主控)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Scheduler   │  │ State Store │  │  Dashboard  │         │
│  │ (cron/systemd)│  │ (SQLite/    │  │ (Grafana/   │         │
│  │             │  │  Parquet)   │  │  Streamlit) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                  │
│         └────────────────┼────────────────┘                  │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              STRATEGY RUNNERS (隔离进程)             │    │
│  │  grid_spot_v1  │  dca_spot_v1  │  arb_funding_v1   │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              OKX CLI WRAPPER (统一执行入口)           │    │
│  └─────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │      OKX API        │
              │  (REST + WebSocket) │
              └─────────────────────┘
```

**云端扩展**：
- 重计算任务（回测、参数扫描、ML 训练）→ 云 GPU 实例
- 高频/低延迟策略 → 云 VPS (东京/新加坡)
- 主控始终在 M1，云端为无状态 Worker

---

## 5. 实施路线图

| 阶段 | 交付物 | 时间预估 | 优先级 |
|------|--------|----------|--------|
| **Phase 1: 基础设施** | 执行引擎、状态存储、基础监控 | 1周 | P0 |
| **Phase 2: 策略标准化** | Grid 参数化、回测框架、风控预检 | 1周 | P0 |
| **Phase 3: 多策略支持** | DCA、资金费率套利、趋势策略 | 2周 | P1 |
| **Phase 4: 智能化** | 参数自动优化、组合再平衡、ML 信号 | 2周 | P2 |
| **Phase 5: 生产级** | 灾备、多账户、合规审计、文档完善 | 1周 | P1 |

---

## 6. 当前状态映射

| 组件 | 现状 | 目标 | Gap |
|------|------|------|-----|
| **执行引擎** | 手动 CLI | 统一 Python Wrapper | 需开发 |
| **策略层** | 单一 Grid 硬编码 | 参数化注册表 | 需重构 |
| **风控层** | 无 | 分级熔断 | 需开发 |
| **数据层** | 无持久化 | 完整数据湖 | 需开发 |
| **监控** | 手动查 CLI | 实时看板+告警 | 需开发 |
| **复盘** | 无 | 标准化 SOP | 需建立 |
| **回测** | 无 | 历史验证框架 | 需开发 |

---

## 7. 下一步行动

1. **立即**：创建 `executor.py` - OKX CLI 统一封装（实盘/模拟切换、重试、幂等）
2. **今日**：创建 `state_store.py` - SQLite + Parquet 状态持久化
3. **明日**：将现有 ETH-BTC Grid 参数化，生成 `params_schema.json` + `default_params.yaml`
4. **本周内**：完成 Phase 1 核心基础设施，跑通「数据→策略→风控→执行→状态同步→监控」全链路

---

## 8. 文件结构规划

```
/Users/leo/Desktop/leohermes/02_Projects/Trading_Automation_System/
├── ARCHITECTURE.md              # 本文件
├── config/
│   ├── accounts.yaml            # 账户配置
│   ├── risk_limits.yaml         # 风控参数
│   └── alerts.yaml              # 告警规则
├── src/
│   ├── executor/                # 执行引擎
│   │   ├── __init__.py
│   │   ├── okx_wrapper.py
│   │   ├── order_manager.py
│   │   └── circuit_breaker.py
│   ├── strategies/              # 策略层
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── grid/
│   │   ├── dca/
│   │   └── arbitrage/
│   ├── risk/                    # 风控层
│   │   ├── __init__.py
│   │   ├── position_sizer.py
│   │   ├── stop_loss.py
│   │   ├── correlation.py
│   │   └── exposure.py
│   ├── data/                    # 数据层
│   │   ├── __init__.py
│   │   ├── market_data.py
│   │   ├── state_store.py
│   │   └── backtest_engine.py
│   ├── monitoring/              # 监控/告警
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── alerting.py
│   │   └── review_engine.py
│   └── scheduler/               # 调度器
│       ├── __init__.py
│       ├── runner.py
│       └── cron_jobs.py
├── strategies/                  # 策略参数配置（运行时）
│   ├── grid_spot_v1/
│   │   ├── params.yaml
│   │   └── state.json
│   └── ...
├── data/                        # 数据存储（运行时生成）
├── logs/                        # 日志
├── backtests/                   # 回测结果
├── tests/                       # 单元/集成测试
├── scripts/                     # 运维脚本
│   ├── deploy.sh
│   ├── backup.sh
│   └── migrate.py
├── requirements.txt
├── pyproject.toml
├── README.md
└── .env.example
```

---

*文档版本控制：所有架构变更需记录在 `CHANGELOG.md`，重大变更需董事长确认。*