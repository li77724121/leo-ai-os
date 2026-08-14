import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RiskManager")

class RiskManager:
    def __init__(self, 
                 max_account_risk: float = 0.02,  # 单笔交易最大账户风险 (2%)
                 max_drawdown_limit: float = 0.10, # 最大账户回撤限制 (10%)
                 default_atr_multiplier: float = 2.0): # ATR 止损倍数
        self.max_account_risk = max_account_risk
        self.max_drawdown_limit = max_drawdown_limit
        self.atr_multiplier = default_atr_multiplier
        self.initial_balance = 0.0

    def set_initial_balance(self, balance: float):
        self.initial_balance = balance
        logger.info(f"Initial balance set to: {balance}")

    def calculate_position_size(self, 
                               current_balance: float, 
                               entry_price: float, 
                               stop_loss_price: float) -> float:
        """
        根据风险百分比计算仓位大小
        Position Size = (Balance * Risk%) / (Entry - StopLoss)
        """
        risk_amount = current_balance * self.max_account_risk
        price_risk = abs(entry_price - stop_loss_price)
        
        if price_risk == 0:
            return 0.0
            
        position_size = risk_amount / price_risk
        logger.info(f"Calculated position size: {position_size:.4f} (Risk: {risk_amount:.2f})")
        return position_size

    def calculate_atr_stop_loss(self, 
                                entry_price: float, 
                                atr: float, 
                                side: str) -> float:
        """
        基于 ATR 计算动态止损线
        """
        if side.upper() == 'BUY':
            return entry_price - (atr * self.atr_multiplier)
        elif side.upper() == 'SELL':
            return entry_price + (atr * self.atr_multiplier)
        return entry_price

    def check_max_drawdown(self, current_balance: float) -> bool:
        """
        检查是否触发最大回撤保护
        """
        if self.initial_balance == 0:
            return False
            
        drawdown = (self.initial_balance - current_balance) / self.initial_balance
        if drawdown >= self.max_drawdown_limit:
            logger.error(f"MAX DRAWDOWN REACHED: {drawdown:.2%}. Trading halted!")
            return True
        return False

    def calculate_kelly_size(self, 
                             win_rate: float, 
                             profit_loss_ratio: float) -> float:
        """
        凯利公式计算最优仓位比例
        f = (bp - q) / b
        b: 盈亏比, p: 胜率, q: 败率
        """
        p = win_rate
        q = 1 - win_rate
        b = profit_loss_ratio
        
        kelly_f = (b * p - q) / b if b != 0 else 0
        # 使用半凯利 (Half-Kelly) 以降低波动
        return max(0, kelly_f * 0.5)

    def update_trailing_stop(self, 
                             current_price: float, 
                             current_stop: float, 
                             side: str, 
                             trailing_step: float) -> float:
        """
        更新追踪止损线
        """
        if side.upper() == 'BUY':
            new_stop = max(current_stop, current_price - trailing_step)
        elif side.upper() == 'SELL':
            new_stop = min(current_stop, current_price + trailing_step)
        else:
            new_stop = current_stop
            
        return new_stop