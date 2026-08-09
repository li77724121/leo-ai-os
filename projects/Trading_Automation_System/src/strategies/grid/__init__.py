"""
现货网格策略实现
"""

from __future__ import annotations
import math
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..base import (
    BaseStrategy, StrategyContext, StrategyState, Order, OrderSide, OrderType,
    MarketData, Position, Trade, generate_cl_ord_id, ExecutionResult
)

logger = logging.getLogger(__name__)


@dataclass
class GridLevel:
    """网格价格层级"""
    index: int                    # 网格索引 (0 = 最低)
    price: float                  # 该层价格
    side: OrderSide               # BUY / SELL
    order: Optional[Order] = None # 当前挂单
    filled: bool = False          # 是否已成交
    qty: float = 0                # 该层数量


class GridSpotStrategy(BaseStrategy):
    """现货网格交易策略"""
    
    STRATEGY_ID = "grid_spot_v1"
    STRATEGY_NAME = "现货网格策略 v1"
    VERSION = "1.0.0"
    PARAMS_SCHEMA_PATH = "strategies/grid_spot_v1/params_schema.json"
    DEFAULT_PARAMS_PATH = "strategies/grid_spot_v1/params.yaml"
    
    def __init__(self, params: Dict[str, Any], context: StrategyContext):
        super().__init__(params, context)
        
        # 解析核心参数
        self.inst_id = params["instId"]
        self.grid_num = params["grid_num"]
        self.min_price = float(params["min_price"])
        self.max_price = float(params["max_price"])
        self.total_investment = float(params["total_investment"])
        self.direction = params.get("direction", "long")
        self.order_type = OrderType(params.get("order_type", "limit"))
        
        # 风控参数
        risk_params = params.get("risk", {})
        self.max_drawdown_pct = risk_params.get("max_drawdown_pct", 0.08)
        
        # 运行时状态
        self.grid_levels: List[GridLevel] = []
        self.grid_initialized = False
        self.base_qty_per_grid: float = 0
        self.quote_qty_per_grid: float = 0
        
        # 价格精度（从市场数据获取）
        self.price_precision: int = 8
        self.size_precision: int = 8
        
        logger.info(f"GridSpotStrategy initialized: {self.inst_id}, grids={self.grid_num}, "
                   f"range=[{self.min_price}, {self.max_price}], investment={self.total_investment}")
    
    def on_init(self, context: StrategyContext) -> None:
        """初始化：计算网格、获取精度、创建初始订单"""
        self.logger.info("Initializing grid strategy...")
        
        # 1. 获取市场精度信息
        self._load_market_precision()
        
        # 2. 计算网格价格层级
        self._calculate_grid_levels()
        
        # 3. 计算每格数量
        self._calculate_grid_quantities()
        
        # 4. 检查当前持仓和挂单
        self._reconcile_existing_state()
        
        # 5. 补全缺失的网格订单
        self._place_missing_grid_orders()
        
        self.grid_initialized = True
        self.context.state = StrategyState.RUNNING
        self.context.started_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        
        self.logger.info(f"Grid initialized: {len(self.grid_levels)} levels, "
                        f"base_per_grid={self.base_qty_per_grid}, quote_per_grid={self.quote_qty_per_grid}")
    
    def _load_market_precision(self):
        """从市场数据加载精度"""
        # TODO: 从 OKX instruments API 获取
        # 暂时使用 ETH-BTC 的默认精度
        if "ETH-BTC" in self.inst_id:
            self.price_precision = 5
            self.size_precision = 5
        elif "BTC-USDT" in self.inst_id:
            self.price_precision = 1
            self.size_precision = 6
        else:
            self.price_precision = 8
            self.size_precision = 8
    
    def _calculate_grid_levels(self):
        """计算等差网格价格层级"""
        # 等差数列：price[i] = min_price + i * step
        step = (self.max_price - self.min_price) / self.grid_num
        
        self.grid_levels = []
        for i in range(self.grid_num + 1):  # n 个网格 = n+1 条价格线
            price = self.min_price + i * step
            price = round(price, self.price_precision)
            
            # 确定买卖方向
            if self.direction == "long":
                # 长网格：下半部买入，上半部卖出
                mid = self.grid_num // 2
                side = OrderSide.BUY if i < mid else OrderSide.SELL
            else:
                # 中性网格：交替买卖
                side = OrderSide.BUY if i % 2 == 0 else OrderSide.SELL
            
            self.grid_levels.append(GridLevel(
                index=i,
                price=price,
                side=side
            ))
        
        self.logger.debug(f"Grid levels: {[f'{g.index}:{g.price}({g.side.value})' for g in self.grid_levels]}")
    
    def _calculate_grid_quantities(self):
        """计算每格数量"""
        if self.direction == "long":
            # 长网格：投入全部为计价货币，买入侧平均分配
            buy_grids = sum(1 for g in self.grid_levels if g.side == OrderSide.BUY)
            if buy_grids > 0:
                self.quote_qty_per_grid = self.total_investment / buy_grids
                # 预估基础货币数量（按中间价）
                mid_price = (self.min_price + self.max_price) / 2
                self.base_qty_per_grid = self.quote_qty_per_grid / mid_price
        else:
            # 中性网格：资金对半分
            buy_grids = sum(1 for g in self.grid_levels if g.side == OrderSide.BUY)
            sell_grids = sum(1 for g in self.grid_levels if g.side == OrderSide.SELL)
            if buy_grids > 0:
                self.quote_qty_per_grid = (self.total_investment / 2) / buy_grids
            if sell_grids > 0:
                mid_price = (self.min_price + self.max_price) / 2
                self.base_qty_per_grid = (self.total_investment / 2) / sell_grids / mid_price
    
    def _reconcile_existing_state(self):
        """对账现有持仓和挂单"""
        # 检查当前持仓
        if self.context.position:
            self.logger.info(f"Current position: {self.context.position.pos} @ {self.context.position.avg_px}")
        
        # 检查现有挂单，映射到网格层级
        for order in self.context.open_orders:
            if order.inst_id != self.inst_id:
                continue
            
            # 找到最接近的网格层级
            best_level = min(
                self.grid_levels,
                key=lambda g: abs(g.price - (order.px or 0))
            )
            if abs(best_level.price - (order.px or 0)) < best_level.price * 0.001:  # 0.1% 容差
                best_level.order = order
                best_level.filled = order.status in (OrderStatus.FILLED, OrderStatus.PARTIAL)
                self.logger.debug(f"Mapped existing order {order.cl_ord_id} to grid level {best_level.index}")
    
    def _place_missing_grid_orders(self) -> List[Order]:
        """补全缺失的网格订单"""
        new_orders = []
        
        for level in self.grid_levels:
            if level.order is not None and level.order.status in (OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL):
                continue  # 已有活跃订单
            
            if level.filled:
                # 已成交，需要反向挂单
                opposite_side = OrderSide.SELL if level.side == OrderSide.BUY else OrderSide.BUY
                # 寻找对应的反向网格
                opposite_level = self._find_opposite_level(level)
                if opposite_level and opposite_level.order is None:
                    order = self._create_grid_order(opposite_level)
                    new_orders.append(order)
            else:
                # 未成交，正常挂单
                order = self._create_grid_order(level)
                new_orders.append(order)
        
        return new_orders
    
    def _find_opposite_level(self, level: GridLevel) -> Optional[GridLevel]:
        """寻找反向网格层级"""
        if level.side == OrderSide.BUY:
            # 买单成交后，在上方卖出
            for g in self.grid_levels:
                if g.side == OrderSide.SELL and g.price > level.price:
                    return g
        else:
            # 卖单成交后，在下方买入
            for g in reversed(self.grid_levels):
                if g.side == OrderSide.BUY and g.price < level.price:
                    return g
        return None
    
    def _create_grid_order(self, level: GridLevel) -> Order:
        """创建网格订单"""
        if level.side == OrderSide.BUY:
            sz = round(self.quote_qty_per_grid / level.price, self.size_precision)
        else:
            sz = round(self.base_qty_per_grid, self.size_precision)
        
        sz = max(sz, self._get_min_order_size())
        
        order = Order(
            cl_ord_id=generate_cl_ord_id(self.STRATEGY_ID, f"grid-{level.index}"),
            inst_id=self.inst_id,
            side=level.side,
            ord_type=self.order_type,
            sz=sz,
            px=round(level.price, self.price_precision),
            td_mode="cash",
            tag=f"grid_{level.index}"
        )
        
        level.order = order
        self.logger.info(f"Created grid order: {order.cl_ord_id} {order.side.value} {order.sz} @ {order.px}")
        return order
    
    def _get_min_order_size(self) -> float:
        """获取最小下单量"""
        # TODO: 从 instruments API 获取
        return 0.00001
    
    def on_tick(self, context: StrategyContext) -> List[Order]:
        """行情更新：检查是否需要补单、止损、止盈"""
        if not self.grid_initialized:
            return []
        
        new_orders = []
        current_price = context.market_data.last_px if context.market_data else 0
        
        # 1. 检查价格是否超出网格区间
        if current_price > self.max_price or current_price < self.min_price:
            self.logger.warning(f"Price {current_price} out of grid range [{self.min_price}, {self.max_price}]")
        
        # 2. 检查风控：回撤
        self._check_drawdown()
        
        # 3. 检查是否有订单需要补单（已成交但反向单未挂）
        for level in self.grid_levels:
            if level.order and level.order.status == OrderStatus.FILLED and not level.filled:
                level.filled = True
                opposite = self._find_opposite_level(level)
                if opposite and opposite.order is None:
                    order = self._create_grid_order(opposite)
                    new_orders.append(order)
        
        # 4. 检查卡单（长时间未成交）
        new_orders.extend(self._check_stuck_orders())
        
        return new_orders
    
    def _check_drawdown(self):
        """检查回撤风控"""
        if self.context.peak_equity > 0:
            current_equity = self.context.peak_equity - self.context.max_drawdown * self.context.peak_equity
            # 实际应该用实时权益
            dd = self.context.max_drawdown
            if dd > self.max_drawdown_pct:
                self.logger.critical(f"Max drawdown exceeded: {dd:.2%} > {self.max_drawdown_pct:.2%}")
                self.context.state = StrategyState.STOPPING
    
    def _check_stuck_orders(self, max_age_sec: int = 3600) -> List[Order]:
        """检查长时间未成交的订单（可选：撤单重挂）"""
        new_orders = []
        now = int(time.time() * 1000)
        
        for level in self.grid_levels:
            if level.order and level.order.status in (OrderStatus.PENDING, OrderStatus.SUBMITTED):
                age = now - level.order.u_time
                if age > max_age_sec * 1000:
                    self.logger.warning(f"Stuck order detected: {level.order.cl_ord_id}, age={age/1000:.0f}s")
                    # 可选：撤单重挂
                    # new_orders.append(cancel_and_replace)
        
        return new_orders
    
    def on_order_update(self, context: StrategyContext, order: Order) -> None:
        """订单状态更新"""
        # 更新网格层级状态
        for level in self.grid_levels:
            if level.order and level.order.cl_ord_id == order.cl_ord_id:
                level.order = order
                if order.status == OrderStatus.FILLED:
                    level.filled = True
                    self.logger.info(f"Grid level {level.index} filled: {order.side.value} {order.sz} @ {order.px}")
                elif order.status in (OrderStatus.CANCELLED, OrderStatus.REJECTED):
                    level.order = None
                    level.filled = False
                break
    
    def on_position_update(self, context: StrategyContext, position: Position) -> None:
        """持仓更新"""
        self.logger.debug(f"Position updated: {position.pos} @ {position.avg_px}, upl={position.upl}")
    
    def on_trade(self, context: StrategyContext, trade: Trade) -> None:
        """成交回调"""
        pnl = 0  # 网格策略单笔成交不直接计算 PnL，由整体持仓计算
        context.record_trade(pnl)
        self.logger.info(f"Trade: {trade.side.value} {trade.sz} @ {trade.px}, fee={trade.fee} {trade.fee_ccy}")
    
    def on_stop(self, context: StrategyContext) -> None:
        """策略停止：撤销所有网格订单"""
        self.logger.info("Stopping grid strategy, cancelling all orders...")
        self.context.state = StrategyState.STOPPING
        
        # 实际撤单由执行引擎处理，这里只标记状态
        for level in self.grid_levels:
            if level.order and level.order.status in (OrderStatus.PENDING, OrderStatus.SUBMITTED):
                level.order.status = OrderStatus.CANCELLED
        
        self.context.state = StrategyState.STOPPED
        self.logger.info("Grid strategy stopped")
    
    def get_grid_status(self) -> Dict[str, Any]:
        """获取网格状态摘要"""
        active = sum(1 for g in self.grid_levels if g.order and g.order.status in (OrderStatus.PENDING, OrderStatus.SUBMITTED))
        filled = sum(1 for g in self.grid_levels if g.filled)
        total_invested = sum(g.order.sz * g.order.px for g in self.grid_levels if g.order and g.order.status == OrderStatus.FILLED and g.order.side == OrderSide.BUY)
        
        return {
            "total_levels": len(self.grid_levels),
            "active_orders": active,
            "filled_levels": filled,
            "total_invested": total_invested,
            "price_range": [self.min_price, self.max_price],
            "current_price": self.context.market_data.last_px if self.context.market_data else None,
            "base_qty_per_grid": self.base_qty_per_grid,
            "quote_qty_per_grid": self.quote_qty_per_grid,
        }


# 导出供注册表使用
__all__ = ["GridSpotStrategy"]