"""
风控模块 - 资金管理、止损、相关性、敞口限制
"""

from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..base import Order, Position, AccountBalance, StrategyContext, OrderSide

logger = logging.getLogger(__name__)


class RiskAction(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    REJECT = "reject"
    REDUCE = "reduce"
    LIQUIDATE = "liquidate"


@dataclass
class RiskCheckResult:
    action: RiskAction
    reason: str
    details: Dict[str, Any]
    current_value: float
    limit_value: float


@dataclass
class RiskLimits:
    """风控限额配置"""
    # 单策略限额
    max_strategy_allocation_pct: float = 0.10      # 单策略占总权益上限
    max_strategy_drawdown_pct: float = 0.15        # 单策略最大回撤
    
    # 单品种限额
    max_instrument_exposure_pct: float = 0.20      # 单品种敞口上限
    max_instrument_correlation: float = 0.70       # 相关性上限
    
    # 账户级限额
    max_account_drawdown_pct: float = 0.10         # 账户最大回撤
    max_total_leverage: float = 3.0                # 总杠杆上限
    min_free_margin_pct: float = 0.10              # 最小可用保证金比例
    
    # 单笔交易限额
    max_order_value_pct: float = 0.05              # 单笔订单占权益上限
    max_slippage_bps: int = 50                     # 最大滑点 (bp)
    
    # 频率限制
    max_orders_per_minute: int = 60
    max_orders_per_hour: int = 1000


class RiskManager:
    """统一风控管理器"""
    
    def __init__(self, limits: RiskLimits = None):
        self.limits = limits or RiskLimits()
        self._order_counts: Dict[str, List[float]] = {}  # 策略ID -> 时间戳列表
        self._correlation_cache: Dict[Tuple[str, str], float] = {}
    
    def check_pre_trade(self, context: StrategyContext, order: Order, 
                       balance: AccountBalance, positions: List[Position]) -> RiskCheckResult:
        """下单前风控检查"""
        
        # 1. 单策略资金占用检查
        result = self._check_strategy_allocation(context, order, balance)
        if result.action != RiskAction.ALLOW:
            return result
        
        # 2. 单品种敞口检查
        result = self._check_instrument_exposure(context, order, balance, positions)
        if result.action != RiskAction.ALLOW:
            return result
        
        # 3. 单笔订单金额检查
        result = self._check_order_size(order, balance)
        if result.action != RiskAction.ALLOW:
            return result
        
        # 4. 频率限制检查
        result = self._check_frequency(context.strategy_id)
        if result.action != RiskAction.ALLOW:
            return result
        
        # 5. 账户整体风险检查
        result = self._check_account_health(balance, positions)
        if result.action != RiskAction.ALLOW:
            return result
        
        return RiskCheckResult(RiskAction.ALLOW, "All checks passed", {}, 0, 0)
    
    def check_post_trade(self, context: StrategyContext, 
                        balance: AccountBalance, positions: List[Position]) -> List[RiskCheckResult]:
        """交易后风控检查（用于监控告警）"""
        results = []
        
        # 策略回撤检查
        results.append(self._check_strategy_drawdown(context))
        
        # 账户回撤检查
        results.append(self._check_account_drawdown(balance))
        
        # 保证金充足性检查
        results.append(self._check_margin_adequacy(balance, positions))
        
        # 相关性检查
        results.append(self._check_portfolio_correlation(positions))
        
        return results
    
    def _check_strategy_allocation(self, context: StrategyContext, order: Order, 
                                   balance: AccountBalance) -> RiskCheckResult:
        """检查单策略资金占用"""
        strategy_equity = self._estimate_strategy_equity(context, balance)
        allocation_pct = strategy_equity / balance.total_eq if balance.total_eq > 0 else 0
        
        if allocation_pct > self.limits.max_strategy_allocation_pct:
            return RiskCheckResult(
                RiskAction.REJECT,
                f"Strategy allocation {allocation_pct:.2%} exceeds limit {self.limits.max_strategy_allocation_pct:.2%}",
                {"strategy_equity": strategy_equity, "total_eq": balance.total_eq},
                allocation_pct, self.limits.max_strategy_allocation_pct
            )
        
        if allocation_pct > self.limits.max_strategy_allocation_pct * 0.8:
            return RiskCheckResult(
                RiskAction.WARN,
                f"Strategy allocation {allocation_pct:.2%} approaching limit",
                {"strategy_equity": strategy_equity, "total_eq": balance.total_eq},
                allocation_pct, self.limits.max_strategy_allocation_pct
            )
        
        return RiskCheckResult(RiskAction.ALLOW, "OK", {}, allocation_pct, self.limits.max_strategy_allocation_pct)
    
    def _check_instrument_exposure(self, context: StrategyContext, order: Order,
                                   balance: AccountBalance, positions: List[Position]) -> RiskCheckResult:
        """检查单品种敞口"""
        # 计算该品种当前敞口 + 新订单敞口
        current_exposure = 0
        for pos in positions:
            if pos.inst_id == order.inst_id:
                current_exposure += abs(pos.pos * pos.mark_px)
        
        # 新订单预估敞口
        order_value = order.sz * (order.px or 0)
        total_exposure = current_exposure + order_value
        exposure_pct = total_exposure / balance.total_eq if balance.total_eq > 0 else 0
        
        if exposure_pct > self.limits.max_instrument_exposure_pct:
            return RiskCheckResult(
                RiskAction.REJECT,
                f"Instrument exposure {exposure_pct:.2%} exceeds limit {self.limits.max_instrument_exposure_pct:.2%}",
                {"instrument": order.inst_id, "current": current_exposure, "order_value": order_value},
                exposure_pct, self.limits.max_instrument_exposure_pct
            )
        
        return RiskCheckResult(RiskAction.ALLOW, "OK", {}, exposure_pct, self.limits.max_instrument_exposure_pct)
    
    def _check_order_size(self, order: Order, balance: AccountBalance) -> RiskCheckResult:
        """检查单笔订单金额"""
        order_value = order.sz * (order.px or 0)
        pct = order_value / balance.total_eq if balance.total_eq > 0 else 0
        
        if pct > self.limits.max_order_value_pct:
            return RiskCheckResult(
                RiskAction.REJECT,
                f"Order value {pct:.2%} exceeds single order limit {self.limits.max_order_value_pct:.2%}",
                {"order_value": order_value, "total_eq": balance.total_eq},
                pct, self.limits.max_order_value_pct
            )
        
        return RiskCheckResult(RiskAction.ALLOW, "OK", {}, pct, self.limits.max_order_value_pct)
    
    def _check_frequency(self, strategy_id: str) -> RiskCheckResult:
        """检查下单频率"""
        now = __import__("time").time()
        window_sec = 60
        
        if strategy_id not in self._order_counts:
            self._order_counts[strategy_id] = []
        
        # 清理过期记录
        self._order_counts[strategy_id] = [
            t for t in self._order_counts[strategy_id] if now - t < window_sec
        ]
        
        current_count = len(self._order_counts[strategy_id])
        
        if current_count >= self.limits.max_orders_per_minute:
            return RiskCheckResult(
                RiskAction.REJECT,
                f"Order frequency {current_count}/min exceeds limit {self.limits.max_orders_per_minute}",
                {"current_count": current_count},
                current_count, self.limits.max_orders_per_minute
            )
        
        # 记录本次下单
        self._order_counts[strategy_id].append(now)
        
        return RiskCheckResult(RiskAction.ALLOW, "OK", {}, current_count, self.limits.max_orders_per_minute)
    
    def _check_account_health(self, balance: AccountBalance, positions: List[Position]) -> RiskCheckResult:
        """检查账户整体健康度"""
        # 计算总杠杆
        total_notional = 0
        total_margin = 0
        
        for pos in positions:
            if pos.pos != 0:
                notional = abs(pos.pos * pos.mark_px)
                total_notional += notional
                if pos.margin_mode == "isolated":
                    total_margin += pos.imr
                else:
                    total_margin += notional / float(pos.lever) if pos.lever else notional
        
        leverage = total_notional / balance.total_eq if balance.total_eq > 0 else 0
        
        if leverage > self.limits.max_total_leverage:
            return RiskCheckResult(
                RiskAction.WARN,
                f"Total leverage {leverage:.2f}x exceeds limit {self.limits.max_total_leverage}x",
                {"total_notional": total_notional, "total_eq": balance.total_eq},
                leverage, self.limits.max_total_leverage
            )
        
        # 可用保证金检查
        # 简化：假设总权益中未占用部分为可用
        used_margin = sum(p.imr for p in positions if p.pos != 0)
        free_margin_pct = (balance.total_eq - used_margin) / balance.total_eq if balance.total_eq > 0 else 1
        
        if free_margin_pct < self.limits.min_free_margin_pct:
            return RiskCheckResult(
                RiskAction.WARN,
                f"Free margin {free_margin_pct:.2%} below minimum {self.limits.min_free_margin_pct:.2%}",
                {"free_margin_pct": free_margin_pct, "used_margin": used_margin},
                free_margin_pct, self.limits.min_free_margin_pct
            )
        
        return RiskCheckResult(RiskAction.ALLOW, "OK", {}, leverage, self.limits.max_total_leverage)
    
    def _check_strategy_drawdown(self, context: StrategyContext) -> RiskCheckResult:
        """检查策略回撤"""
        dd = context.max_drawdown
        limit = self.limits.max_strategy_drawdown_pct
        
        if dd > limit:
            return RiskCheckResult(
                RiskAction.LIQUIDATE,
                f"Strategy drawdown {dd:.2%} exceeds limit {limit:.2%} - LIQUIDATE",
                {"strategy_id": context.strategy_id, "drawdown": dd},
                dd, limit
            )
        elif dd > limit * 0.8:
            return RiskCheckResult(
                RiskAction.WARN,
                f"Strategy drawdown {dd:.2%} approaching limit {limit:.2%}",
                {"strategy_id": context.strategy_id, "drawdown": dd},
                dd, limit
            )
        
        return RiskCheckResult(RiskAction.ALLOW, "OK", {}, dd, limit)
    
    def _check_account_drawdown(self, balance: AccountBalance) -> RiskCheckResult:
        """检查账户回撤"""
        # 需要历史峰值，这里简化处理
        # 实际应该从 StateStore 获取历史峰值
        return RiskCheckResult(RiskAction.ALLOW, "Account drawdown check requires historical peak", {}, 0, self.limits.max_account_drawdown_pct)
    
    def _check_margin_adequacy(self, balance: AccountBalance, positions: List[Position]) -> RiskCheckResult:
        """检查保证金充足性"""
        total_mm = sum(p.mmr for p in positions if p.pos != 0)
        margin_ratio = balance.total_eq / total_mm if total_mm > 0 else float('inf')
        
        if margin_ratio < 2.0:  # 保证金率 < 200%
            return RiskCheckResult(
                RiskAction.WARN if margin_ratio > 1.5 else RiskAction.REDUCE,
                f"Margin ratio {margin_ratio:.2f} below safe threshold",
                {"margin_ratio": margin_ratio, "total_mm": total_mm},
                margin_ratio, 2.0
            )
        
        return RiskCheckResult(RiskAction.ALLOW, "OK", {}, margin_ratio, 2.0)
    
    def _check_portfolio_correlation(self, positions: List[Position]) -> RiskCheckResult:
        """检查组合相关性"""
        # 简化实现：检查是否有过多高相关品种
        # 实际需要历史价格数据计算相关系数矩阵
        instruments = list(set(p.inst_id for p in positions if p.pos != 0))
        
        if len(instruments) > 5:
            return RiskCheckResult(
                RiskAction.WARN,
                f"Portfolio has {len(instruments)} instruments, correlation risk increases",
                {"instruments": instruments},
                len(instruments), 5
            )
        
        return RiskCheckResult(RiskAction.ALLOW, "OK", {}, len(instruments), 5)
    
    def _estimate_strategy_equity(self, context: StrategyContext, balance: AccountBalance) -> float:
        """估算策略占用权益"""
        # 简化：用策略参数中的投入金额 + 未实现盈亏
        invested = context.params.get("total_investment", 0) or context.params.get("investment", 0)
        return invested + context.unrealized_pnl
    
    def calculate_position_size(self, balance: AccountBalance, 
                               risk_pct: float, entry_price: float, 
                               stop_loss_price: float) -> float:
        """凯利公式 / 固定风险仓位计算"""
        risk_per_unit = abs(entry_price - stop_loss_price)
        if risk_per_unit == 0:
            return 0
        
        risk_amount = balance.total_eq * risk_pct
        position_size = risk_amount / risk_per_unit
        
        # 限制不超过单策略上限
        max_size = balance.total_eq * self.limits.max_strategy_allocation_pct / entry_price
        return min(position_size, max_size)
    
    def should_reduce_position(self, context: StrategyContext, 
                              balance: AccountBalance) -> Tuple[bool, str]:
        """判断是否需要减仓"""
        checks = self.check_post_trade(context, balance, [])
        for check in checks:
            if check.action in (RiskAction.REDUCE, RiskAction.LIQUIDATE):
                return True, check.reason
        return False, ""


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
        self.state = "CLOSED"  # CLOSED / OPEN / HALF_OPEN
        self.failure_count = 0
        self.last_failure_time = 0
        self.failure_threshold = 5
        self.recovery_timeout = 300  # 5分钟
    
    def check_and_update(self, context: StrategyContext, balance: AccountBalance, 
                        positions: List[Position]) -> bool:
        """检查并更新熔断状态，返回是否允许交易"""
        if self.state == "OPEN":
            # 检查是否可以尝试恢复
            if __import__("time").time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker: HALF_OPEN - attempting recovery")
            else:
                return False
        
        # 运行风控检查
        results = self.risk_manager.check_post_trade(context, balance, positions)
        
        critical_count = sum(1 for r in results if r.action == RiskAction.LIQUIDATE)
        
        if critical_count > 0:
            self.failure_count += critical_count
            self.last_failure_time = __import__("time").time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.critical(f"Circuit breaker OPENED after {self.failure_count} critical failures")
                return False
        else:
            # 成功重置计数
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit breaker CLOSED - recovery successful")
            self.failure_count = max(0, self.failure_count - 1)
        
        return self.state != "OPEN"
    
    def force_open(self, reason: str):
        """强制熔断"""
        self.state = "OPEN"
        self.last_failure_time = __import__("time").time()
        logger.critical(f"Circuit breaker FORCED OPEN: {reason}")
    
    def force_close(self):
        """强制关闭熔断"""
        self.state = "CLOSED"
        self.failure_count = 0
        logger.info("Circuit breaker FORCED CLOSE")