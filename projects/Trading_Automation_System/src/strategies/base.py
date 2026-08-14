"""
交易自动化系统 - 基础核心模块
定义策略基类、数据结构、执行接口
"""

from __future__ import annotations
import json
import uuid
import time
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal
from pathlib import Path
import yaml
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# 枚举与常量
# ============================================================================

class StrategyState(str, Enum):
    """策略生命周期状态"""
    INIT = "init"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    POST_ONLY = "post_only"
    FOK = "fok"
    IOC = "ioc"


class OrderStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class AlgoOrderType(str, Enum):
    GRID = "grid"
    DCA = "dca"
    CONDITIONAL = "conditional"
    OCO = "oco"
    TRAILING = "trailing"


class ExecutionMode(str, Enum):
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ============================================================================
# 核心数据结构
# ============================================================================

@dataclass
class MarketData:
    """行情数据"""
    inst_id: str
    timestamp: int
    last_px: float
    bid_px: float
    ask_px: float
    bid_sz: float
    ask_sz: float
    volume_24h: float
    turnover_24h: float
    high_24h: float
    low_24h: float
    funding_rate: Optional[float] = None
    next_funding_time: Optional[int] = None


@dataclass
class Position:
    """持仓"""
    inst_id: str
    inst_type: str
    pos_side: str          # long / short / net
    pos: float             # 持仓数量
    avg_px: float          # 开仓均价
    mark_px: float         # 标记价格
    upl: float             # 未实现盈亏
    upl_ratio: float       # 未实现收益率
    imr: float             # 初始保证金
    mmr: float             # 维持保证金
    margin_mode: str       # cross / isolated
    lever: str             # 杠杆倍数
    liq_px: Optional[float] = None
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))


@dataclass
class Order:
    """订单"""
    cl_ord_id: str                     # 客户端订单ID (幂等键)
    inst_id: str
    side: OrderSide
    ord_type: OrderType
    sz: float
    px: Optional[float] = None
    td_mode: str = "cash"              # cash / cross / isolated
    pos_side: Optional[str] = None     # long / short
    tag: Optional[str] = None
    reduce_only: bool = False
    status: OrderStatus = OrderStatus.PENDING
    ord_id: Optional[str] = None       # 交易所订单ID
    filled_sz: float = 0
    avg_px: float = 0
    fee: float = 0
    fee_ccy: str = ""
    state: str = "live"
    c_time: int = field(default_factory=lambda: int(time.time() * 1000))
    u_time: int = field(default_factory=lambda: int(time.time() * 1000))
    error_code: Optional[str] = None
    error_msg: Optional[str] = None


@dataclass
class AlgoOrder:
    """策略单 (Grid/DCA/条件单等)"""
    algo_id: str
    algo_cl_ord_id: str
    inst_id: str
    algo_type: AlgoOrderType
    params: Dict[str, Any]
    state: str                         # running / paused / stopped
    c_time: int
    u_time: int
    investment: float = 0
    profit: float = 0
    trade_num: int = 0


@dataclass
class AccountBalance:
    """账户余额"""
    total_eq: float          # 总权益 USD
    iso_eq: float            # 逐仓权益
    adj_eq: float            # 调整权益
    details: Dict[str, Dict]  # 各币种详情
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))


@dataclass
class Trade:
    """成交记录"""
    trade_id: str
    inst_id: str
    ord_id: str
    cl_ord_id: str
    side: OrderSide
    px: float
    sz: float
    fee: float
    fee_ccy: str
    pos_side: str
    td_mode: str
    exec_type: str         # T / M / F
    timestamp: int


# ============================================================================
# 上下文对象
# ============================================================================

@dataclass
class StrategyContext:
    """策略运行时上下文"""
    strategy_id: str
    strategy_name: str
    version: str
    params: Dict[str, Any]
    state: StrategyState = StrategyState.INIT
    state_data: Dict[str, Any] = field(default_factory=dict)
    
    # 运行时数据
    market_data: Optional[MarketData] = None
    position: Optional[Position] = None
    balance: Optional[AccountBalance] = None
    open_orders: List[Order] = field(default_factory=list)
    algo_orders: List[AlgoOrder] = field(default_factory=list)
    recent_trades: List[Trade] = field(default_factory=list)
    
    # 统计指标
    total_pnl: float = 0
    realized_pnl: float = 0
    unrealized_pnl: float = 0
    trade_count: int = 0
    win_count: int = 0
    max_drawdown: float = 0
    peak_equity: float = 0
    
    # 时间
    started_at: Optional[datetime] = None
    last_update: Optional[datetime] = None
    
    def update_equity(self, current_equity: float):
        """更新权益峰值和回撤"""
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        if self.peak_equity > 0:
            dd = (self.peak_equity - current_equity) / self.peak_equity
            if dd > self.max_drawdown:
                self.max_drawdown = dd
    
    def record_trade(self, pnl: float):
        self.trade_count += 1
        self.realized_pnl += pnl
        if pnl > 0:
            self.win_count += 1
    
    @property
    def win_rate(self) -> float:
        return self.win_count / self.trade_count if self.trade_count > 0 else 0


# ============================================================================
# 策略基类
# ============================================================================

class BaseStrategy(ABC):
    """所有策略的基类"""
    
    # 类属性：策略元数据
    STRATEGY_ID: str = ""
    STRATEGY_NAME: str = ""
    VERSION: str = "1.0.0"
    PARAMS_SCHEMA_PATH: str = ""
    DEFAULT_PARAMS_PATH: str = ""
    
    def __init__(self, params: Dict[str, Any], context: StrategyContext):
        self.params = params
        self.context = context
        self.logger = logging.getLogger(f"strategy.{self.STRATEGY_ID}")
        self._validate_params()
    
    def _validate_params(self):
        """参数校验"""
        if self.PARAMS_SCHEMA_PATH:
            schema_path = Path(self.PARAMS_SCHEMA_PATH)
            if schema_path.exists():
                with open(schema_path) as f:
                    schema = json.load(f)
                try:
                    validate(instance=self.params, schema=schema)
                except ValidationError as e:
                    raise ValueError(f"参数校验失败: {e.message}")
    
    @abstractmethod
    def on_init(self, context: StrategyContext) -> None:
        """策略初始化：订阅行情、加载状态、创建初始订单"""
        pass
    
    @abstractmethod
    def on_tick(self, context: StrategyContext) -> List[Order]:
        """每个行情更新调用：返回需要下发的订单列表"""
        pass
    
    @abstractmethod
    def on_order_update(self, context: StrategyContext, order: Order) -> None:
        """订单状态更新回调"""
        pass
    
    @abstractmethod
    def on_position_update(self, context: StrategyContext, position: Position) -> None:
        """持仓更新回调"""
        pass
    
    @abstractmethod
    def on_trade(self, context: StrategyContext, trade: Trade) -> None:
        """成交回调"""
        pass
    
    @abstractmethod
    def on_stop(self, context: StrategyContext) -> None:
        """策略停止：撤单、保存状态、清理资源"""
        pass
    
    def on_error(self, context: StrategyContext, error: Exception) -> None:
        """错误处理"""
        self.logger.error(f"Strategy error: {error}", exc_info=True)
        self.context.state = StrategyState.ERROR
    
    def get_required_data(self) -> List[str]:
        """声明需要的数据类型，供数据层预加载"""
        return ["market_data", "position", "balance"]
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """获取策略状态快照，用于持久化"""
        return {
            "strategy_id": self.STRATEGY_ID,
            "version": self.VERSION,
            "params": self.params,
            "context_state": asdict(self.context),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def load_state(self, state: Dict[str, Any]) -> None:
        """从快照恢复状态"""
        self.context.state = StrategyState(state.get("context_state", {}).get("state", "init"))
        self.context.state_data = state.get("context_state", {}).get("state_data", {})


# ============================================================================
# 参数加载器
# ============================================================================

class ParamLoader:
    """策略参数加载与验证"""
    
    @staticmethod
    def load_yaml(path: Union[str, Path]) -> Dict[str, Any]:
        with open(path) as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def load_json(path: Union[str, Path]) -> Dict[str, Any]:
        with open(path) as f:
            return json.load(f)
    
    @staticmethod
    def validate(params: Dict[str, Any], schema_path: Union[str, Path]) -> tuple[bool, Optional[str]]:
        schema = ParamLoader.load_json(schema_path)
        try:
            validate(instance=params, schema=schema)
            return True, None
        except ValidationError as e:
            return False, e.message
    
    @staticmethod
    def merge_with_defaults(params: Dict[str, Any], defaults_path: Union[str, Path]) -> Dict[str, Any]:
        defaults = ParamLoader.load_yaml(defaults_path)
        return ParamLoader._deep_merge(defaults, params)
    
    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        result = base.copy()
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = ParamLoader._deep_merge(result[k], v)
            else:
                result[k] = v
        return result


# ============================================================================
# 策略注册表
# ============================================================================

class StrategyRegistry:
    """策略注册与发现"""
    
    _strategies: Dict[str, type] = {}
    
    @classmethod
    def register(cls, strategy_class: type) -> type:
        if not issubclass(strategy_class, BaseStrategy):
            raise TypeError("Must inherit from BaseStrategy")
        if not strategy_class.STRATEGY_ID:
            raise ValueError("STRATEGY_ID is required")
        cls._strategies[strategy_class.STRATEGY_ID] = strategy_class
        logger.info(f"Registered strategy: {strategy_class.STRATEGY_ID} v{strategy_class.VERSION}")
        return strategy_class
    
    @classmethod
    def get(cls, strategy_id: str) -> Optional[type]:
        return cls._strategies.get(strategy_id)
    
    @classmethod
    def list_all(cls) -> List[Dict[str, Any]]:
        return [
            {
                "strategy_id": s.STRATEGY_ID,
                "name": s.STRATEGY_NAME,
                "version": s.VERSION,
                "schema": s.PARAMS_SCHEMA_PATH,
                "defaults": s.DEFAULT_PARAMS_PATH
            }
            for s in cls._strategies.values()
        ]
    
    @classmethod
    def create_instance(cls, strategy_id: str, params: Dict, context: StrategyContext) -> BaseStrategy:
        strategy_class = cls.get(strategy_id)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_id}")
        return strategy_class(params, context)


# ============================================================================
# 幂等订单 ID 生成器
# ============================================================================

def generate_cl_ord_id(strategy_id: str, suffix: str = "") -> str:
    """生成幂等客户端订单 ID"""
    timestamp = int(time.time() * 1000)
    unique = uuid.uuid4().hex[:8]
    parts = [strategy_id, str(timestamp), unique]
    if suffix:
        parts.append(suffix)
    return "-".join(parts)


# ============================================================================
# 结果封装
# ============================================================================

@dataclass
class ExecutionResult:
    success: bool
    data: Any = None
    error_code: Optional[str] = None
    error_msg: Optional[str] = None
    latency_ms: float = 0
    
    @classmethod
    def ok(cls, data: Any = None, latency_ms: float = 0) -> ExecutionResult:
        return cls(success=True, data=data, latency_ms=latency_ms)
    
    @classmethod
    def err(cls, error_code: str, error_msg: str, latency_ms: float = 0) -> ExecutionResult:
        return cls(success=False, error_code=error_code, error_msg=error_msg, latency_ms=latency_ms)