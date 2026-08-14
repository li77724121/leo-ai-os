#!/usr/bin/env python3
"""
策略运行器启动脚本
用法: python runner.py --strategy grid_spot_v1 --params strategies/grid_spot_v1/params.yaml
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.runner import StrategyRunner, RunnerConfig
from src.strategies.registry import discover_strategies

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Trading Automation System - Strategy Runner")
    parser.add_argument("--strategy", required=True, help="Strategy ID (e.g., grid_spot_v1)")
    parser.add_argument("--params", required=True, help="Path to strategy params YAML")
    parser.add_argument("--profile", default="okx-live", help="OKX CLI profile")
    parser.add_argument("--demo", action="store_true", help="Use demo mode")
    parser.add_argument("--db", default="data/state.db", help="State database path")
    parser.add_argument("--tick-interval", type=float, default=1.0, help="Main loop interval (sec)")
    parser.add_argument("--sync-interval", type=int, default=30, help="State sync interval (sec)")
    parser.add_argument("--alert-config", default="config/alerts.yaml", help="Alert config path")
    parser.add_argument("--no-alerts", action="store_true", help="Disable alerts")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--list-strategies", action="store_true", help="List available strategies")
    
    args = parser.parse_args()
    
    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # 列出策略
    if args.list_strategies:
        strategies = discover_strategies()
        print("Available strategies:")
        for s in strategies:
            print(f"  {s}")
        return 0
    
    # 验证策略
    if args.strategy not in discover_strategies():
        logger.error(f"Unknown strategy: {args.strategy}")
        logger.info(f"Available: {discover_strategies()}")
        return 1
    
    # 验证参数文件
    params_path = Path(args.params)
    if not params_path.exists():
        logger.error(f"Params file not found: {params_path}")
        return 1
    
    # 创建配置
    from src.risk.risk_manager import RiskLimits
    
    config = RunnerConfig(
        strategy_id=args.strategy,
        params_path=str(params_path),
        okx_profile=args.profile,
        okx_demo=args.demo,
        db_path=args.db,
        tick_interval_sec=args.tick_interval,
        sync_interval_sec=args.sync_interval,
        alert_config_path=args.alert_config,
        enable_alerts=not args.no_alerts,
        risk_limits=RiskLimits()  # 可从配置文件加载
    )
    
    # 创建并启动运行器
    runner = StrategyRunner(config)
    
    try:
        logger.info(f"Starting strategy: {args.strategy}")
        logger.info(f"Params: {params_path}")
        logger.info(f"Profile: {args.profile} (demo={args.demo})")
        
        runner.start()
        
        # 主线程等待
        import threading
        while runner._running:
            threading.Event().wait(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Runner error: {e}", exc_info=True)
        return 1
    finally:
        logger.info("Shutting down...")
        runner.stop()
        logger.info("Stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())