# Trading Automation System

> 个人量化交易自动化系统 - 从单一策略到策略工厂的完整基础设施

## 🎯 核心目标

- **标准化**：策略参数化、可配置、可复用、可版本管理
- **自动化**：行情获取 → 信号计算 → 风控检查 → 订单执行 → 状态同步 → 监控告警 → 复盘分析
- **可观测**：实时看板、分级告警、标准化复盘报告（日/周/月）
- **安全第一**：多层风控、熔断机制、资金保护优先于收益最大化
- **可扩展**：插件式策略架构，支持 Grid/DCA/套利/趋势/因子等多策略并行

---

## 🏗 系统架构

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

## 📁 项目结构

```
Trading_Automation_System/
├── ARCHITECTURE.md              # 架构设计文档
├── runner.py                    # 启动入口
├── requirements.txt             # 依赖
├── config/
│   ├── risk_limits.yaml         # 风控限额
│   └── alerts.yaml              # 告警规则
├── strategies/                  # 策略参数配置（运行时）
│   └── grid_spot_v1/
│       ├── params.yaml          # 策略参数
│       └── params_schema.json   # JSON Schema 验证
├── src/
│   ├── strategies/              # 策略层
│   │   ├── base.py              # 基类与核心数据结构
│   │   ├── registry.py          # 策略注册表
│   │   └── grid/                # 网格策略实现
│   ├── executor/                # 执行层
│   │   └── okx_wrapper.py       # OKX CLI 统一封装
│   ├── data/                    # 数据层
│   │   └── state_store.py       # SQLite + Parquet 存储
│   ├── risk/                    # 风控层
│   │   └── risk_manager.py      # 风控引擎 + 熔断器
│   ├── monitoring/              # 监控/告警/复盘
│   │   └── alerting.py          # 指标收集、告警、看板、报告
│   └── scheduler/               # 调度器
│       └── runner.py            # 单/多策略运行器
├── data/                        # 运行时数据（自动生成）
│   ├── state.db                 # SQLite 状态库
│   └── backtests/               # 回测/导出数据
├── logs/                        # 日志
└── tests/                       # 测试
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 OKX CLI
npm install -g @okx_ai/okx-trade-cli

# 配置 OKX API Key
okx config init

# 安装 Python 依赖
cd /Users/leo/Desktop/leohermes/02_Projects/Trading_Automation_System
pip install -r requirements.txt
```

### 2. 验证账户

```bash
# 检查实盘账户
okx --profile okx-live account balance

# 检查现有策略
okx --profile okx-live bot grid orders --algoOrdType grid
```

### 3. 启动策略

```bash
# 启动 ETH-BTC 现货网格（实盘）
python runner.py --strategy grid_spot_v1 --params strategies/grid_spot_v1/params.yaml

# 启动模拟盘测试
python runner.py --strategy grid_spot_v1 --params strategies/grid_spot_v1/params.yaml --demo

# 查看可用策略
python runner.py --list-strategies
```

### 4. 监控与告警

```bash
# 配置 Telegram 告警（环境变量）
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# 启动时自动加载 config/alerts.yaml
```

---

## 📊 策略参数化示例

### Grid Spot v1 (`strategies/grid_spot_v1/params.yaml`)

```yaml
metadata:
  strategy_id: "grid_spot_v1"
  strategy_name: "现货网格策略 v1"
  version: "1.0.0"

trading:
  inst_id: "ETH-BTC"
  inst_type: "SPOT"
  grid:
    upper_price: 0.2000
    lower_price: 0.0100
    grid_count: 16
  investment:
    quote_ccy: "BTC"
    total_investment: 0.0015
  direction: "long"

risk:
  max_drawdown_pct: 0.08
  stop_loss:
    enabled: false
  capital:
    max_allocation_pct: 0.10

execution:
  mode: "live"
  sync:
    interval_sec: 30
```

所有参数通过 `params_schema.json` 严格验证，支持版本管理和回测参数扫描。

---

## 🛡 风控体系

| 层级 | 检查项 | 动作 |
|------|--------|------|
| **L1 策略** | 单策略回撤 > 8% | 告警 |
| **L2 策略** | 单策略回撤 > 12% | 停止开仓 |
| **L3 策略** | 单策略回撤 > 15% | 全部平仓、停止策略 |
| **账户** | 账户回撤 > 10% | 全市场熔断 |
| **敞口** | 单品种 > 20% 权益 | 拒单 |
| **相关性** | 高相关策略合计 > 15% | 预警 |
| **杠杆** | 总杠杆 > 3x | 预警/减仓 |
| **频率** | > 30 单/分 | 限流 |

---

## 📈 复盘 SOP

### 日报（每日 00:05 UTC）
- 市场概览、策略 PnL、成交统计、风险检查、执行质量

### 周报（每周一 00:00 UTC）
- 收益归因、参数优化回测、容量评估、系统健康

### 月报（每月 1 号 00:00 UTC）
- 组合优化、资本再平衡、基建成本、知识沉淀

报告自动生成至 `data/backtests/{run_id}/`，包含：
- `report.html` - 可视化报告
- `equity_curve.parquet` - 权益曲线
- `trades.parquet` - 成交明细

---

## 🔧 开发指南

### 添加新策略

1. 在 `src/strategies/` 下创建策略模块
2. 继承 `BaseStrategy` 实现抽象方法
3. 用 `@StrategyRegistry.register` 装饰器注册
4. 在 `strategies/` 下创建 `params.yaml` 和 `params_schema.json`
5. 运行 `python runner.py --strategy your_strategy_id --params ...`

### 运行回测

```python
from src.data.state_store import StateStore
from src.monitoring.alerting import ReviewEngine

store = StateStore("data/state.db")
review = ReviewEngine(store, get_metrics_collector())

# 生成日报
report = review.generate_daily_report("grid_spot_v1-xxx", datetime(2025, 6, 29))
```

### 自定义告警

编辑 `config/alerts.yaml`，支持的上下文变量：
- `strategy.drawdown_pct` - 策略回撤
- `strategy.total_pnl` - 策略总盈亏
- `account.drawdown_pct` - 账户回撤
- `risk.margin_ratio` - 保证金率
- `system.api_latency_ms` - API 延迟

---

## 📦 部署建议

### 开发/测试
- Mac Mini M1 本地运行
- `--demo` 模式验证逻辑
- SQLite 本地存储

### 生产环境
- 主控：Mac Mini M1（定时任务、状态管理、监控）
- 执行：OKX CLI 直连（低延迟、高可靠）
- 重计算：云 GPU（回测、参数扫描、ML 训练）
- 高频：云 VPS 东京/新加坡（亚毫秒延迟）

### 系统服务化

```ini
# /etc/systemd/system/trading-grid.service
[Unit]
Description=Trading Grid Strategy
After=network.target

[Service]
Type=simple
User=leo
WorkingDirectory=/Users/leo/Desktop/leohermes/02_Projects/Trading_Automation_System
ExecStart=/usr/bin/python3 runner.py --strategy grid_spot_v1 --params strategies/grid_spot_v1/params.yaml
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-grid
sudo systemctl start trading-grid
```

---

## 🗺 路线图

| 阶段 | 交付物 | 状态 |
|------|--------|------|
| **Phase 1: 基础设施** | 执行引擎、状态存储、基础监控、Grid 标准化 | ✅ 完成 |
| **Phase 2: 多策略** | DCA、资金费率套利、趋势策略、组合管理 | 🔄 进行中 |
| **Phase 3: 智能化** | 参数自动优化、ML 信号、动态风控 | 📋 规划中 |
| **Phase 4: 生产级** | 灾备、多账户、合规审计、文档完善 | 📋 规划中 |

---

## ⚠️ 免责声明

**本系统仅供学习和研究使用。实盘交易涉及真实资金风险，请务必：**

1. 充分回测验证策略逻辑
2. 设置合理的风控限额
3. 小资金实盘跑通全流程后再加大资金
4. 定期复盘并根据市场变化调整参数
5. **作者不对任何交易损失负责**

---

## 📄 许可证

MIT License - 详见 LICENSE 文件