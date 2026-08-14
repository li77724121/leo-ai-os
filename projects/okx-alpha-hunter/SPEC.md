# Project: OKX Alpha Hunter (欧易 Alpha 捕捉系统)

## 1. 核心愿景 (Core Vision)
构建一个全自动的量化抄币系统，通过监控大户行为、社交信号和量化指标，在欧易 (OKX) 平台上捕捉高胜率的 Alpha 机会，实现资产的快速增长。

## 2. 第一原则分析 (First Principles Analysis)
- **本质**：信息差 $\rightarrow$ 速度 $\rightarrow$ 概率 $\rightarrow$ 收益。
- **核心竞争力**：
    - **极速响应**：从信号产生到下单的延迟最小化。
    - **信号纯度**：通过多维度过滤（链上+社交+量化）剔除噪音。
    - **严格风控**：用数学模型管理风险，而非依赖直觉。

## 3. 功能模块 (Functional Modules)
### 3.1 信号监控层 (Signal Monitoring)
- **OKX API 监听**：实时监控特定币种的成交量异常和价格波动。
- **Whale Watcher**：追踪高胜率地址的资金流向。
- **Social Signal**：监控 X/Telegram 的关键 KOL 信号。

### 3.2 决策引擎 (Decision Engine)
- **信号聚合**：将量化指标、社交情绪、资金流向进行加权评分。
- **买入触发**：当综合评分超过阈值时，触发买入指令。
- **风险评估**：计算当前仓位风险，决定下单金额。

### 3.3 执行层 (Execution Layer)
- **API 交易接口**：实现快速下单、撤单、平仓。
- **风控模块**：自动执行止损和止盈逻辑。

## 4. 技术栈 (Technical Stack)
- **语言**: Python 3.11+ (异步处理 `asyncio`)
- **库**: `ccxt` (标准加密货币交易库), `pandas` (数据分析), `ta-lib` (技术指标)
- **数据库**: Redis (实时信号缓存) + PostgreSQL (交易记录与策略回测)
- **AI 层**: LLM (用于分析社交信号的语义)

## 5. 执行路线图 (Roadmap)
- [ ] **Phase 1: 基础连接** (OKX API 接入 $\rightarrow$ 基础行情获取)。
- [ ] **Phase 2: 信号构建** (实现大户追踪 $\rightarrow$ 量化指标计算)。
- [ ] **Phase 3: 自动化交易** (实现下单逻辑 $\rightarrow$ 基础风控)。
- [ ] **Phase 4: 策略优化** (回测 $\rightarrow$ 参数调优 $\rightarrow$ 实盘运行)。