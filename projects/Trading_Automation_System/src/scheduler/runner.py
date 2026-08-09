"""
策略运行器 - 统筹策略、执行、风控、监控、状态存储
"""

from __future__ import annotations
import logging
import time
import threading
import uuid
import signal
import sys
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import yaml

from .strategies.base import (
    BaseStrategy, StrategyContext, StrategyState, StrategyRegistry,
    MarketData, Position, Order, Trade, AccountBalance, AlgoOrder, generate_cl_ord_id
)
from .executor.okx_wrapper import OKXExecutor, OKXConfig
from .data.state_store import StateStore, get_state_store
from .risk.risk_manager import RiskManager, RiskLimits, CircuitBreaker
from .monitoring.alerting import (
    MetricsCollector, AlertEngine, AlertRule, AlertLevel,
    DashboardDataProvider, ReviewEngine, get_metrics_collector, get_alert_engine
)

logger = logging.getLogger(__name__)


@dataclass
class RunnerConfig:
    """运行器配置"""
    # 策略配置
    strategy_id: str
    params_path: str
    
    # 执行配置
    okx_profile: str = "okx-live"
    okx_demo: bool = False
    
    # 存储配置
    db_path: str = "data/state.db"
    
    # 风控配置
    risk_limits: RiskLimits = None
    
    # 运行配置
    tick_interval_sec: float = 1.0       # 主循环间隔
    sync_interval_sec: int = 30          # 状态同步间隔
    health_check_interval_sec: int = 60  # 健康检查间隔
    
    # 监控配置
    enable_alerts: bool = True
    alert_config_path: str = "config/alerts.yaml"
    
    # 优雅关闭
    shutdown_timeout_sec: int = 30


class StrategyRunner:
    """单策略运行器"""
    
    def __init__(self, config: RunnerConfig):
        self.config = config
        self.run_id = f"{config.strategy_id}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # 核心组件
        self.executor: Optional[OKXExecutor] = None
        self.store: Optional[StateStore] = None
        self.strategy: Optional[BaseStrategy] = None
        self.context: Optional[StrategyContext] = None
        self.risk_manager: Optional[RiskManager] = None
        self.circuit_breaker: Optional[CircuitBreaker] = None
        self.metrics: Optional[MetricsCollector] = None
        self.alert_engine: Optional[AlertEngine] = None
        self.dashboard: Optional[DashboardDataProvider] = None
        self.review: Optional[ReviewEngine] = None
        
        # 运行状态
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._sync_thread: Optional[threading.Thread] = None
        self._last_tick = 0
        self._last_sync = 0
        self._last_health_check = 0
        
        # 线程池
        self._executor_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix=f"runner-{config.strategy_id}")
        
        # 信号处理
        self._setup_signals()
    
    def _setup_signals(self):
        """注册信号处理"""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
    
    def initialize(self) -> bool:
        """初始化所有组件"""
        try:
            logger.info(f"Initializing runner {self.run_id} for strategy {self.config.strategy_id}")
            
            # 1. 加载策略参数
            params = self._load_params()
            
            # 2. 初始化执行器
            self.executor = OKXExecutor(OKXConfig(
                profile=self.config.okx_profile,
                demo=self.config.okx_demo
            ))
            
            # 3. 初始化状态存储
            self.store = StateStore(self.config.db_path)
            
            # 4. 创建策略运行记录
            self.store.create_strategy_run(self.run_id, self.config.strategy_id, "1.0.0", params)
            
            # 5. 初始化策略上下文
            self.context = StrategyContext(
                strategy_id=self.config.strategy_id,
                strategy_name=self.config.strategy_id,
                version="1.0.0",
                params=params
            )
            
            # 6. 创建策略实例
            self.strategy = StrategyRegistry.create_instance(
                self.config.strategy_id, params, self.context
            )
            
            # 7. 初始化风控
            self.risk_manager = RiskManager(self.config.risk_limits or RiskLimits())
            self.circuit_breaker = CircuitBreaker(self.risk_manager)
            
            # 8. 初始化监控
            self.metrics = get_metrics_collector()
            self.alert_engine = get_alert_engine()
            self.dashboard = DashboardDataProvider(self.metrics)
            self.review = ReviewEngine(self.store, self.metrics)
            
            # 加载告警规则
            if self.config.enable_alerts:
                self._load_alert_rules()
            
            # 9. 初始同步状态
            self._sync_state()
            
            # 10. 策略初始化
            self.strategy.on_init(self.context)
            
            logger.info(f"Runner {self.run_id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Runner initialization failed: {e}", exc_info=True)
            return False
    
    def _load_params(self) -> Dict[str, Any]:
        """加载并合并参数"""
        from .strategies.base import ParamLoader
        from .strategies.registry import get_strategy_info
        
        info = get_strategy_info(self.config.strategy_id)
        if not info:
            raise ValueError(f"Unknown strategy: {self.config.strategy_id}")
        
        # 加载用户参数
        user_params = ParamLoader.load_yaml(self.config.params_path)
        
        # 合并默认参数
        if info["defaults_path"]:
            defaults = ParamLoader.load_yaml(info["defaults_path"])
            params = ParamLoader._deep_merge(defaults, user_params)
        else:
            params = user_params
        
        # 验证
        if info["schema_path"]:
            valid, err = ParamLoader.validate(params, info["schema_path"])
            if not valid:
                raise ValueError(f"Parameter validation failed: {err}")
        
        return params
    
    def _load_alert_rules(self):
        """加载告警规则"""
        path = Path(self.config.alert_config_path)
        if not path.exists():
            logger.warning(f"Alert config not found: {path}")
            return
        
        with open(path) as f:
            config = yaml.safe_load(f)
        
        for rule_config in config.get("alerts", []):
            rule = AlertRule(**rule_config)
            self.alert_engine.add_rule(rule)
        
        logger.info(f"Loaded {len(config.get('alerts', []))} alert rules")
    
    def _sync_state(self):
        """同步账户、持仓、订单、策略单状态"""
        try:
            # 同步余额
            bal_result = self.executor.get_balance()
            if bal_result.success:
                balance = self._parse_balance(bal_result.data)
                self.context.balance = balance
                self.store.save_account_snapshot(self.run_id, balance)
                
                # 记录指标
                self.metrics.record_gauge("account.total_eq", balance.total_eq, {"run_id": self.run_id})
                self.metrics.record_gauge("account.available_eq", balance.adj_eq, {"run_id": self.run_id})
            
            # 同步现货持仓
            pos_result = self.executor.get_positions("SPOT")
            if pos_result.success:
                positions = self._parse_positions(pos_result.data, "SPOT")
                for pos in positions:
                    self.context.position = pos  # 简化：只保留主要持仓
                    self.store.save_position_snapshot(self.run_id, pos)
                    self.metrics.record_gauge(f"position.{pos.inst_id}.pos", pos.pos, {"run_id": self.run_id})
                    self.metrics.record_gauge(f"position.{pos.inst_id}.upl", pos.upl, {"run_id": self.run_id})
            
            # 同步合约持仓
            swap_pos_result = self.executor.get_positions("SWAP")
            if swap_pos_result.success:
                positions = self._parse_positions(swap_pos_result.data, "SWAP")
                for pos in positions:
                    self.store.save_position_snapshot(self.run_id, pos)
            
            # 同步活跃订单
            orders_result = self.executor.get_spot_orders(state="open")
            if orders_result.success:
                orders = self._parse_orders(orders_result.data)
                self.context.open_orders = orders
                self.store.save_orders_batch(self.run_id, orders, self.config.strategy_id)
                self.metrics.record_gauge("orders.open_count", len(orders), {"run_id": self.run_id})
            
            # 同步策略单
            grid_result = self.executor.get_grid_orders()
            if grid_result.success:
                algos = self._parse_algo_orders(grid_result.data)
                self.context.algo_orders = algos
                for algo in algos:
                    self.store.save_algo_order(self.run_id, algo, self.config.strategy_id)
            
            logger.debug(f"State sync completed for {self.run_id}")
            
        except Exception as e:
            logger.error(f"State sync failed: {e}", exc_info=True)
    
    def _parse_balance(self, data: List[Dict]) -> AccountBalance:
        """解析余额数据"""
        total_eq = 0
        details = {}
        for item in data[0].get("details", []) if data else []:
            ccy = item.get("ccy", "")
            eq = float(item.get("eq", 0))
            avail = float(item.get("availBal", 0) or item.get("availEq", 0))
            frozen = float(item.get("frozenBal", 0))
            details[ccy] = {"eq": eq, "avail": avail, "frozen": frozen, **item}
            total_eq += float(item.get("eqUsd", 0) or 0)
        
        # 如果没有 eqUsd，尝试从总层级获取
        if total_eq == 0 and data:
            total_eq = float(data[0].get("totalEq", 0))
        
        return AccountBalance(
            total_eq=total_eq,
            iso_eq=float(data[0].get("isoEq", 0)) if data else 0,
            adj_eq=float(data[0].get("adjEq", 0)) if data else 0,
            details=details
        )
    
    def _parse_positions(self, data: List[Dict], inst_type: str) -> List[Position]:
        """解析持仓数据"""
        positions = []
        for item in data:
            try:
                pos = Position(
                    inst_id=item.get("instId", ""),
                    inst_type=inst_type,
                    pos_side=item.get("posSide", "net"),
                    pos=float(item.get("pos", 0)),
                    avg_px=float(item.get("avgPx", 0)),
                    mark_px=float(item.get("markPx", 0)),
                    upl=float(item.get("upl", 0)),
                    upl_ratio=float(item.get("uplRatio", 0)),
                    imr=float(item.get("imr", 0)),
                    mmr=float(item.get("mmr", 0)),
                    margin_mode=item.get("mgnMode", "cross"),
                    lever=item.get("lever", ""),
                    liq_px=float(item.get("liqPx", 0)) if item.get("liqPx") else None,
                    timestamp=int(item.get("uTime", 0) or time.time() * 1000)
                )
                if pos.pos != 0:
                    positions.append(pos)
            except Exception as e:
                logger.warning(f"Failed to parse position: {e}")
        return positions
    
    def _parse_orders(self, data: List[Dict]) -> List[Order]:
        """解析订单数据"""
        orders = []
        for item in data:
            try:
                order = Order(
                    cl_ord_id=item.get("clOrdId", ""),
                    ord_id=item.get("ordId", ""),
                    inst_id=item.get("instId", ""),
                    side=item.get("side", "buy"),
                    ord_type=item.get("ordType", "limit"),
                    sz=float(item.get("sz", 0)),
                    px=float(item.get("px", 0)) if item.get("px") else None,
                    td_mode=item.get("tdMode", "cash"),
                    pos_side=item.get("posSide"),
                    status=item.get("state", "live"),
                    filled_sz=float(item.get("fillSz", 0) or item.get("accFillSz", 0)),
                    avg_px=float(item.get("avgPx", 0)) if item.get("avgPx") else 0,
                    fee=float(item.get("fee", 0)),
                    fee_ccy=item.get("feeCcy", ""),
                    tag=item.get("tag", ""),
                    c_time=int(item.get("cTime", 0)),
                    u_time=int(item.get("uTime", 0))
                )
                orders.append(order)
            except Exception as e:
                logger.warning(f"Failed to parse order: {e}")
        return orders
    
    def _parse_algo_orders(self, data: List[Dict]) -> List[AlgoOrder]:
        """解析策略单数据"""
        algos = []
        for item in data:
            try:
                algo = AlgoOrder(
                    algo_id=item.get("algoId", ""),
                    algo_cl_ord_id=item.get("algoClOrdId", ""),
                    inst_id=item.get("instId", ""),
                    algo_type=item.get("algoOrdType", "grid"),
                    params=item,  # 保存完整参数
                    state=item.get("state", "running"),
                    investment=float(item.get("investment", 0)),
                    profit=float(item.get("profit", 0) or item.get("gridProfit", 0)),
                    trade_num=int(item.get("tradeNum", 0)),
                    c_time=int(item.get("cTime", 0)),
                    u_time=int(item.get("uTime", 0))
                )
                algos.append(algo)
            except Exception as e:
                logger.warning(f"Failed to parse algo order: {e}")
        return algos
    
    def start(self):
        """启动运行器"""
        if self._running:
            logger.warning("Runner already running")
            return
        
        if not self.initialize():
            raise RuntimeError("Runner initialization failed")
        
        self._running = True
        self.context.state = StrategyState.RUNNING
        self.context.started_at = datetime.now(timezone.utc)
        
        # 启动主循环线程
        self._thread = threading.Thread(target=self._main_loop, name=f"runner-{self.config.strategy_id}", daemon=True)
        self._thread.start()
        
        # 启动同步线程
        self._sync_thread = threading.Thread(target=self._sync_loop, name=f"sync-{self.config.strategy_id}", daemon=True)
        self._sync_thread.start()
        
        logger.info(f"Runner {self.run_id} started")
    
    def stop(self):
        """停止运行器"""
        if not self._running:
            return
        
        logger.info(f"Stopping runner {self.run_id}...")
        self._running = False
        self.context.state = StrategyState.STOPPING
        
        # 等待主循环结束
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.config.shutdown_timeout_sec)
        
        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=10)
        
        # 策略清理
        if self.strategy:
            self.strategy.on_stop(self.context)
        
        # 更新运行记录
        self.store.update_strategy_state(self.run_id, StrategyState.STOPPED, self.context.state_data)
        
        # 导出数据
        try:
            self.store.export_to_parquet(self.run_id, f"data/backtests/{self.run_id}")
        except Exception as e:
            logger.warning(f"Export failed: {e}")
        
        # 关闭线程池
        self._executor_pool.shutdown(wait=True)
        
        self.context.state = StrategyState.STOPPED
        logger.info(f"Runner {self.run_id} stopped")
    
    def _main_loop(self):
        """主循环：行情 -> 策略 -> 风控 -> 执行 -> 状态更新"""
        logger.info("Main loop started")
        
        while self._running:
            loop_start = time.time()
            
            try:
                # 1. 检查熔断器
                if self.circuit_breaker and not self.circuit_breaker.check_and_update(
                    self.context, self.context.balance or AccountBalance(0,0,0,{}), 
                    [self.context.position] if self.context.position else []
                ):
                    logger.warning("Circuit breaker OPEN, pausing strategy")
                    self.context.state = StrategyState.PAUSED
                    time.sleep(10)
                    continue
                
                if self.context.state != StrategyState.RUNNING:
                    time.sleep(1)
                    continue
                
                # 2. 获取行情
                ticker_result = self.executor.get_ticker(self.context.params.get("instId", ""))
                if ticker_result.success:
                    market_data = self._parse_ticker(ticker_result.data)
                    self.context.market_data = market_data
                    self.context.last_update = datetime.now(timezone.utc)
                    
                    # 记录行情指标
                    self.metrics.record_gauge(f"market.{market_data.inst_id}.last_px", market_data.last_px, {"run_id": self.run_id})
                    self.metrics.record_gauge(f"market.{market_data.inst_id}.bid_ask_spread", market_data.ask_px - market_data.bid_px, {"run_id": self.run_id})
                
                # 3. 策略计算
                if self.strategy:
                    new_orders = self.strategy.on_tick(self.context)
                    
                    # 4. 风控检查 & 执行
                    for order in new_orders:
                        if self.context.balance:
                            check = self.risk_manager.check_pre_trade(self.context, order, self.context.balance, 
                                                                     [self.context.position] if self.context.position else [])
                            if check.action == RiskAction.ALLOW:
                                self._execute_order(order)
                            elif check.action == RiskAction.WARN:
                                logger.warning(f"Risk warn: {check.reason}")
                                self._execute_order(order)
                            else:
                                logger.error(f"Risk reject: {check.reason}")
                                order.status = OrderStatus.REJECTED
                                order.error_msg = check.reason
                                self.store.save_order(self.run_id, order, self.config.strategy_id)
                
                # 5. 更新策略指标
                self._update_strategy_metrics()
                
                # 6. 告警评估
                if self.alert_engine:
                    self.alert_engine.evaluate(self._build_alert_context())
                
            except Exception as e:
                logger.error(f"Main loop error: {e}", exc_info=True)
                if self.strategy:
                    self.strategy.on_error(self.context, e)
            
            # 控制循环频率
            elapsed = time.time() - loop_start
            sleep_time = max(0, self.config.tick_interval_sec - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        logger.info("Main loop ended")
    
    def _sync_loop(self):
        """状态同步循环"""
        while self._running:
            time.sleep(self.config.sync_interval_sec)
            if self._running:
                self._sync_state()
    
    def _execute_order(self, order: Order):
        """执行订单"""
        try:
            # 根据订单类型路由
            if order.ord_type in (OrderType.MARKET, OrderType.LIMIT, OrderType.POST_ONLY):
                if self.context.params.get("instType", "SPOT") == "SPOT":
                    result = self.executor.place_spot_order(
                        inst_id=order.inst_id,
                        side=order.side,
                        ord_type=order.ord_type,
                        sz=order.sz,
                        px=order.px,
                        tgt_ccy="base_ccy",
                        cl_ord_id=order.cl_ord_id,
                        tag=order.tag
                    )
                else:
                    result = self.executor.place_swap_order(
                        inst_id=order.inst_id,
                        side=order.side,
                        ord_type=order.ord_type,
                        sz=order.sz,
                        px=order.px,
                        td_mode=order.td_mode,
                        pos_side=order.pos_side or "net",
                        tgt_ccy="base_ccy",
                        cl_ord_id=order.cl_ord_id,
                        tag=order.tag
                    )
                
                if result.success:
                    order.status = OrderStatus.SUBMITTED
                    order.ord_id = result.data.get("ordId") if isinstance(result.data, dict) else None
                else:
                    order.status = OrderStatus.REJECTED
                    order.error_code = result.error_code
                    order.error_msg = result.error_msg
                
                order.u_time = int(time.time() * 1000)
                self.store.save_order(self.run_id, order, self.config.strategy_id)
                
                # 触发策略回调
                if self.strategy:
                    self.strategy.on_order_update(self.context, order)
                    
        except Exception as e:
            logger.error(f"Order execution failed: {e}", exc_info=True)
            order.status = OrderStatus.REJECTED
            order.error_msg = str(e)
            self.store.save_order(self.run_id, order, self.config.strategy_id)
    
    def _parse_ticker(self, data: List[Dict]) -> MarketData:
        item = data[0] if data else {}
        return MarketData(
            inst_id=item.get("instId", ""),
            timestamp=int(item.get("ts", 0) or time.time() * 1000),
            last_px=float(item.get("last", 0)),
            bid_px=float(item.get("bidPx", 0)),
            ask_px=float(item.get("askPx", 0)),
            bid_sz=float(item.get("bidSz", 0)),
            ask_sz=float(item.get("askSz", 0)),
            volume_24h=float(item.get("vol24h", 0)),
            turnover_24h=float(item.get("volCcy24h", 0)),
            high_24h=float(item.get("high24h", 0)),
            low_24h=float(item.get("low24h", 0))
        )
    
    def _update_strategy_metrics(self):
        """更新策略级指标"""
        self.metrics.record_gauge(f"strategy.{self.config.strategy_id}.state", 
                                 1 if self.context.state == StrategyState.RUNNING else 0, 
                                 {"run_id": self.run_id})
        self.metrics.record_gauge(f"strategy.{self.config.strategy_id}.total_pnl", 
                                 self.context.total_pnl, {"run_id": self.run_id})
        self.metrics.record_gauge(f"strategy.{self.config.strategy_id}.drawdown", 
                                 self.context.max_drawdown, {"run_id": self.run_id})
        self.metrics.record_gauge(f"strategy.{self.config.strategy_id}.trade_count", 
                                 self.context.trade_count, {"run_id": self.run_id})
        self.metrics.record_gauge(f"strategy.{self.config.strategy_id}.win_rate", 
                                 self.context.win_rate, {"run_id": self.run_id})
        
        # 网格特有指标
        if hasattr(self.strategy, "get_grid_status"):
            status = self.strategy.get_grid_status()
            for k, v in status.items():
                if isinstance(v, (int, float)):
                    self.metrics.record_gauge(f"strategy.{self.config.strategy_id}.grid.{k}", v, {"run_id": self.run_id})
    
    def _build_alert_context(self) -> Dict[str, Any]:
        """构建告警评估上下文"""
        return {
            "strategy": {
                "drawdown_pct": self.context.max_drawdown,
                "total_pnl": self.context.total_pnl,
                "trade_count": self.context.trade_count,
                "win_rate": self.context.win_rate,
            },
            "account": {
                "total_eq": self.context.balance.total_eq if self.context.balance else 0,
                "drawdown_pct": 0,  # TODO
            },
            "risk": {
                "current_drawdown": self.context.max_drawdown,
                "leverage": 0,
            },
            "system": {
                "api_latency_ms": 0,
                "api_error_rate": 0,
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取运行器状态"""
        return {
            "run_id": self.run_id,
            "strategy_id": self.config.strategy_id,
            "state": self.context.state.value if self.context else "unknown",
            "running": self._running,
            "uptime_sec": (datetime.now(timezone.utc) - self.context.started_at).total_seconds() if self.context and self.context.started_at else 0,
            "last_sync": self._last_sync,
            "metrics": self.dashboard.get_dashboard_snapshot() if self.dashboard else {},
            "circuit_breaker": self.circuit_breaker.state if self.circuit_breaker else "unknown"
        }


class MultiStrategyManager:
    """多策略管理器"""
    
    def __init__(self, base_config: RunnerConfig = None):
        self.base_config = base_config or RunnerConfig(
            strategy_id="", params_path="", db_path="data/state.db"
        )
        self.runners: Dict[str, StrategyRunner] = {}
        self._lock = threading.Lock()
    
    def add_strategy(self, strategy_id: str, params_path: str, **overrides) -> StrategyRunner:
        """添加并启动策略"""
        with self._lock:
            if strategy_id in self.runners:
                raise ValueError(f"Strategy {strategy_id} already running")
            
            config = RunnerConfig(
                strategy_id=strategy_id,
                params_path=params_path,
                okx_profile=self.base_config.okx_profile,
                okx_demo=self.base_config.okx_demo,
                db_path=self.base_config.db_path,
                risk_limits=self.base_config.risk_limits,
                **overrides
            )
            
            runner = StrategyRunner(config)
            self.runners[strategy_id] = runner
            runner.start()
            
            logger.info(f"Added strategy {strategy_id}")
            return runner
    
    def remove_strategy(self, strategy_id: str, graceful: bool = True):
        """移除策略"""
        with self._lock:
            runner = self.runners.pop(strategy_id, None)
            if runner:
                if graceful:
                    runner.stop()
                logger.info(f"Removed strategy {strategy_id}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取所有策略状态"""
        with self._lock:
            return {
                "total": len(self.runners),
                "running": sum(1 for r in self.runners.values() if r._running),
                "strategies": {sid: r.get_status() for sid, r in self.runners.items()}
            }
    
    def stop_all(self):
        """停止所有策略"""
        with self._lock:
            for runner in self.runners.values():
                runner.stop()
            self.runners.clear()


# 便捷函数
def create_runner(strategy_id: str, params_path: str, **kwargs) -> StrategyRunner:
    """创建并初始化单策略运行器（不自动启动）"""
    config = RunnerConfig(strategy_id=strategy_id, params_path=params_path, **kwargs)
    return StrategyRunner(config)