# ==========================================
# OKX 网格抄币系统 - Grid配置 (150U强化版)
# ==========================================

# 资金配置 (150U 网格资金 - BOSS 2026-08-06 指示加大)
TOTAL_CAPITAL = 150.0        # 网格总资金 (USDT)
TRADE_USDT_PER_GRID = 15.0   # 每层USDT (7层 × 15 = 105U, 保留缓冲)
MIN_SOL_TRADE = 0.01         # 最小SOL交易量 (OKX现货最小0.01 SOL)

# SOL网格范围 ($70-85, 7层) - 更密集覆盖
SOL_GRID_LOW = 70.0
SOL_GRID_HIGH = 85.0
GRID_LEVELS = 7              # 网格层数: 70, 72.5, 75, 77.5, 80, 82.5, 85
GRID_PRICES = [70.0, 72.5, 75.0, 77.5, 80.0, 82.5, 85.0]  # 每层价格 (2.5间隔)

# 风控
STOP_LOSS = 0.08            # 止损 8% (防止单边下跌)
TAKE_PROFIT = 0.25          # 止盈 25%
MAX_POSITION_USDT = 150.0    # 单笔最大 (150U)

# 运行设置
CHECK_INTERVAL = 20         # 扫描间隔 20秒 (降低频率)
LOG_FILE = "grid_trader.log"

# 安全开关
LIVE_TRADING_ENABLED = True   # ✅ 启用实盘交易
DRY_RUN = False              # ❌ 关闭模拟交易

# 监控币种
WATCH_SYMBOLS = ["SOL/USDT"]
