"""
策略注册表 - 自动发现与注册
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from .base import StrategyRegistry, BaseStrategy

logger = __import__("logging").getLogger(__name__)


def discover_strategies(package_path: str = "src.strategies") -> List[str]:
    """自动发现并注册所有策略"""
    discovered = []
    
    # 导入 grid 策略
    try:
        from .grid import GridSpotStrategy
        discovered.append("grid_spot_v1")
    except ImportError:
        pass
    
    # 导入 dca 策略
    try:
        from .dca import DCASpotStrategy
        discovered.append("dca_spot_v1")
    except ImportError:
        pass
    
    # 导入套利策略
    try:
        from .arbitrage import FundingRateArbitrageStrategy
        discovered.append("arb_funding_v1")
    except ImportError:
        pass
    
    logger.info(f"Discovered strategies: {discovered}")
    return discovered


def get_strategy_info(strategy_id: str) -> Optional[Dict[str, Any]]:
    """获取策略元信息"""
    strategy_class = StrategyRegistry.get(strategy_id)
    if not strategy_class:
        return None
    
    return {
        "strategy_id": strategy_class.STRATEGY_ID,
        "name": strategy_class.STRATEGY_NAME,
        "version": strategy_class.VERSION,
        "schema_path": strategy_class.PARAMS_SCHEMA_PATH,
        "defaults_path": strategy_class.DEFAULT_PARAMS_PATH,
    }


def list_all_strategies() -> List[Dict[str, Any]]:
    """列出所有已注册策略"""
    return StrategyRegistry.list_all()


# 便捷函数
def create_strategy(strategy_id: str, params: Dict, context) -> BaseStrategy:
    """创建策略实例"""
    return StrategyRegistry.create_instance(strategy_id, params, context)