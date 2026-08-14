"""
OKX 执行引擎 - 统一封装 OKX CLI
支持实盘/模拟盘切换、重试、幂等、状态同步
"""

from __future__ import annotations
import json
import subprocess
import time
import logging
import shlex
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from .base import (
    Order, OrderSide, OrderType, OrderStatus, Position, AlgoOrder, AlgoOrderType,
    AccountBalance, Trade, MarketData, ExecutionResult, generate_cl_ord_id
)

logger = logging.getLogger(__name__)


class OKXProfile(Enum):
    LIVE = "okx-live"
    DEMO = "okx-demo"


@dataclass
class OKXConfig:
    profile: str = "okx-live"
    demo: bool = False
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    cli_path: str = "okx"  # 可配置完整路径


class OKXExecutor:
    """OKX 统一执行接口"""
    
    def __init__(self, config: OKXConfig = None):
        self.config = config or OKXConfig()
        self._lock = threading.Lock()
        self._verify_cli()
        self._verify_auth()
    
    def _verify_cli(self):
        """验证 CLI 可用"""
        try:
            result = subprocess.run(
                [self.config.cli_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError(f"OKX CLI not found: {result.stderr}")
            logger.info(f"OKX CLI version: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError(f"OKX CLI not found at {self.config.cli_path}. Install with: npm install -g @okx_ai/okx-trade-cli")
    
    def _verify_auth(self):
        """验证认证状态"""
        # 检查配置文件
        result = self._run_cmd(["config", "show", "--json"])
        if result.success:
            config_data = json.loads(result.data)
            profiles = config_data.get("profiles", {})
            if self.config.profile not in profiles:
                raise RuntimeError(f"Profile '{self.config.profile}' not found in OKX config")
            profile = profiles[self.config.profile]
            if not profile.get("api_key"):
                raise RuntimeError(f"Profile '{self.config.profile}' has no API key")
            self.config.demo = profile.get("demo", False)
            logger.info(f"Auth verified: profile={self.config.profile}, demo={self.config.demo}")
        else:
            raise RuntimeError(f"Failed to verify auth: {result.error_msg}")
    
    def _run_cmd(self, args: List[str], timeout: Optional[int] = None) -> ExecutionResult:
        """执行 OKX CLI 命令"""
        cmd = [self.config.cli_path]
        
        # 添加 profile 或 demo 标志
        if self.config.demo:
            cmd.append("--demo")
        else:
            cmd.extend(["--profile", self.config.profile])
        
        cmd.extend(args)
        cmd.extend(["--json"])  # 统一 JSON 输出
        
        start = time.time()
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Running: {' '.join(shlex.quote(c) for c in cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout or self.config.timeout
                )
                latency = (time.time() - start) * 1000
                
                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout)
                        return ExecutionResult.ok(data, latency)
                    except json.JSONDecodeError:
                        return ExecutionResult.ok(result.stdout, latency)
                else:
                    last_error = result.stderr
                    logger.warning(f"Command failed (attempt {attempt+1}/{self.config.max_retries}): {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                last_error = "Command timeout"
                logger.warning(f"Command timeout (attempt {attempt+1}/{self.config.max_retries})")
            except Exception as e:
                last_error = str(e)
                logger.error(f"Command error: {e}")
            
            if attempt < self.config.max_retries - 1:
                time.sleep(self.config.retry_delay * (attempt + 1))
        
        return ExecutionResult.err("EXEC_FAILED", last_error or "Unknown error", (time.time() - start) * 1000)
    
    # ========================================================================
    # 账户查询
    # ========================================================================
    
    def get_balance(self) -> ExecutionResult:
        """获取账户余额"""
        return self._run_cmd(["account", "balance"])
    
    def get_positions(self, inst_type: str = None) -> ExecutionResult:
        """获取持仓"""
        args = ["account", "positions"]
        if inst_type:
            args.extend(["--instType", inst_type])
        return self._run_cmd(args)
    
    def get_account_config(self) -> ExecutionResult:
        """获取账户配置"""
        return self._run_cmd(["account", "config"])
    
    # ========================================================================
    # 现货订单
    # ========================================================================
    
    def place_spot_order(
        self,
        inst_id: str,
        side: OrderSide,
        ord_type: OrderType,
        sz: float,
        px: Optional[float] = None,
        tgt_ccy: str = "base_ccy",
        cl_ord_id: Optional[str] = None,
        tag: Optional[str] = None
    ) -> ExecutionResult:
        """下现货单"""
        args = [
            "spot", "place",
            "--instId", inst_id,
            "--side", side.value,
            "--ordType", ord_type.value,
            "--sz", str(sz),
            "--tgtCcy", tgt_ccy
        ]
        
        if px is not None:
            args.extend(["--px", str(px)])
        if cl_ord_id:
            args.extend(["--clOrdId", cl_ord_id])
        if tag:
            args.extend(["--tag", tag])
        
        return self._run_cmd(args)
    
    def cancel_spot_order(self, inst_id: str, ord_id: str = None, cl_ord_id: str = None) -> ExecutionResult:
        """撤现货单"""
        args = ["spot", "cancel", "--instId", inst_id]
        if ord_id:
            args.extend(["--ordId", ord_id])
        if cl_ord_id:
            args.extend(["--clOrdId", cl_ord_id])
        return self._run_cmd(args)
    
    def amend_spot_order(self, inst_id: str, ord_id: str = None, cl_ord_id: str = None, 
                         new_px: float = None, new_sz: float = None) -> ExecutionResult:
        """改现货单"""
        args = ["spot", "amend", "--instId", inst_id]
        if ord_id:
            args.extend(["--ordId", ord_id])
        if cl_ord_id:
            args.extend(["--clOrdId", cl_ord_id])
        if new_px is not None:
            args.extend(["--px", str(new_px)])
        if new_sz is not None:
            args.extend(["--sz", str(new_sz)])
        return self._run_cmd(args)
    
    def get_spot_orders(self, inst_id: str = None, state: str = "open") -> ExecutionResult:
        """查现货订单"""
        args = ["spot", "orders", "--state", state]
        if inst_id:
            args.extend(["--instId", inst_id])
        return self._run_cmd(args)
    
    def get_spot_fills(self, inst_id: str = None, after: str = None, before: str = None, limit: int = 100) -> ExecutionResult:
        """现货成交记录"""
        args = ["spot", "fills", "--limit", str(limit)]
        if inst_id:
            args.extend(["--instId", inst_id])
        if after:
            args.extend(["--after", after])
        if before:
            args.extend(["--before", before])
        return self._run_cmd(args)
    
    # ========================================================================
    # 合约/永续订单
    # ========================================================================
    
    def place_swap_order(
        self,
        inst_id: str,
        side: OrderSide,
        ord_type: OrderType,
        sz: float,
        px: Optional[float] = None,
        td_mode: str = "cross",
        pos_side: str = "net",
        tgt_ccy: str = "base_ccy",
        lever: Optional[str] = None,
        cl_ord_id: Optional[str] = None,
        tp_trigger_px: Optional[float] = None,
        tp_ord_px: Optional[float] = None,
        sl_trigger_px: Optional[float] = None,
        sl_ord_px: Optional[float] = None,
        tag: Optional[str] = None
    ) -> ExecutionResult:
        """下永续合约单"""
        args = [
            "swap", "place",
            "--instId", inst_id,
            "--side", side.value,
            "--ordType", ord_type.value,
            "--sz", str(sz),
            "--tdMode", td_mode,
            "--posSide", pos_side,
            "--tgtCcy", tgt_ccy
        ]
        
        if px is not None:
            args.extend(["--px", str(px)])
        if lever:
            args.extend(["--lever", lever])
        if cl_ord_id:
            args.extend(["--clOrdId", cl_ord_id])
        if tag:
            args.extend(["--tag", tag])
        
        # 附带止盈止损
        if tp_trigger_px is not None:
            args.extend(["--tpTriggerPx", str(tp_trigger_px)])
            if tp_ord_px is not None:
                args.extend(["--tpOrdPx", str(tp_ord_px)])
        if sl_trigger_px is not None:
            args.extend(["--slTriggerPx", str(sl_trigger_px)])
            if sl_ord_px is not None:
                args.extend(["--slOrdPx", str(sl_ord_px)])
        
        return self._run_cmd(args)
    
    def close_swap_position(self, inst_id: str, mgn_mode: str, pos_side: str) -> ExecutionResult:
        """平永续仓位"""
        return self._run_cmd([
            "swap", "close",
            "--instId", inst_id,
            "--mgnMode", mgn_mode,
            "--posSide", pos_side
        ])
    
    def set_swap_leverage(self, inst_id: str, lever: int, mgn_mode: str, pos_side: str = None) -> ExecutionResult:
        """设置合约杠杆"""
        args = [
            "swap", "leverage",
            "--instId", inst_id,
            "--lever", str(lever),
            "--mgnMode", mgn_mode
        ]
        if pos_side:
            args.extend(["--posSide", pos_side])
        return self._run_cmd(args)
    
    def get_swap_positions(self, inst_id: str = None) -> ExecutionResult:
        """查永续持仓"""
        args = ["swap", "positions"]
        if inst_id:
            args.extend(["--instId", inst_id])
        return self._run_cmd(args)
    
    def get_swap_orders(self, inst_id: str = None, state: str = "open") -> ExecutionResult:
        """查永续订单"""
        args = ["swap", "orders", "--state", state]
        if inst_id:
            args.extend(["--instId", inst_id])
        return self._run_cmd(args)
    
    # ========================================================================
    # 策略单
    # ========================================================================
    
    def start_grid(self, params: Dict[str, Any]) -> ExecutionResult:
        """启动网格策略"""
        args = ["bot", "grid", "create"]
        
        # 必需参数
        required = ["instId", "algoOrdType", "gridNum", "minPx", "maxPx", "investment", "runType"]
        for key in required:
            if key not in params:
                return ExecutionResult.err("INVALID_PARAM", f"Missing required param: {key}")
            args.extend([f"--{self._camel_to_kebab(key)}", str(params[key])])
        
        # 可选参数
        optional = ["lever", "tdMode", "posSide", "slTriggerPx", "tpTriggerPx", "tag"]
        for key in optional:
            if key in params and params[key] not in (None, ""):
                args.extend([f"--{self._camel_to_kebab(key)}", str(params[key])])
        
        return self._run_cmd(args)
    
    def stop_grid(self, algo_id: str, algo_ord_type: str = "grid") -> ExecutionResult:
        """停止网格策略"""
        return self._run_cmd([
            "bot", "grid", "stop",
            "--algoId", algo_id,
            "--algoOrdType", algo_ord_type
        ])
    
    def get_grid_orders(self, algo_ord_type: str = "grid", state: str = "running") -> ExecutionResult:
        """查网格策略列表"""
        return self._run_cmd([
            "bot", "grid", "orders",
            "--algoOrdType", algo_ord_type,
            "--state", state
        ])
    
    def get_grid_detail(self, algo_id: str, algo_ord_type: str = "grid") -> ExecutionResult:
        """查网格策略详情"""
        return self._run_cmd([
            "bot", "grid", "details",
            "--algoId", algo_id,
            "--algoOrdType", algo_ord_type
        ])
    
    def start_dca(self, params: Dict[str, Any]) -> ExecutionResult:
        """启动 DCA 策略"""
        args = ["bot", "dca", "create"]
        
        required = ["instId", "algoOrdType", "sz", "px", "interval", "runType"]
        for key in required:
            if key not in params:
                return ExecutionResult.err("INVALID_PARAM", f"Missing required param: {key}")
            args.extend([f"--{self._camel_to_kebab(key)}", str(params[key])])
        
        optional = ["lever", "tdMode", "posSide", "tag"]
        for key in optional:
            if key in params and params[key] not in (None, ""):
                args.extend([f"--{self._camel_to_kebab(key)}", str(params[key])])
        
        return self._run_cmd(args)
    
    # ========================================================================
    # 行情数据
    # ========================================================================
    
    def get_ticker(self, inst_id: str) -> ExecutionResult:
        """获取单个行情"""
        return self._run_cmd(["market", "ticker", "--instId", inst_id])
    
    def get_tickers(self, inst_type: str = "SPOT") -> ExecutionResult:
        """获取所有行情"""
        return self._run_cmd(["market", "tickers", "--instType", inst_type])
    
    def get_candles(self, inst_id: str, bar: str = "1m", limit: int = 100) -> ExecutionResult:
        """获取 K 线"""
        return self._run_cmd([
            "market", "candles",
            "--instId", inst_id,
            "--bar", bar,
            "--limit", str(limit)
        ])
    
    def get_instruments(self, inst_type: str = "SPOT") -> ExecutionResult:
        """获取合约信息（含精度、杠杆等）"""
        return self._run_cmd(["market", "instruments", "--instType", inst_type])
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def _camel_to_kebab(self, s: str) -> str:
        """camelCase 转 kebab-case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', s)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
    
    def sync_all_state(self) -> Dict[str, Any]:
        """全量状态同步"""
        results = {}
        
        # 余额
        bal = self.get_balance()
        results["balance"] = bal.data if bal.success else bal.error_msg
        
        # 现货持仓
        pos = self.get_positions("SPOT")
        results["spot_positions"] = pos.data if pos.success else pos.error_msg
        
        # 合约持仓
        swap_pos = self.get_positions("SWAP")
        results["swap_positions"] = swap_pos.data if swap_pos.success else swap_pos.error_msg
        
        # 活跃策略单
        grid = self.get_grid_orders()
        results["grid_bots"] = grid.data if grid.success else grid.error_msg
        
        return results


# ============================================================================
# 便捷函数
# ============================================================================

_default_executor: Optional[OKXExecutor] = None

def get_executor(profile: str = "okx-live", demo: bool = False) -> OKXExecutor:
    """获取全局执行器实例"""
    global _default_executor
    if _default_executor is None:
        _default_executor = OKXExecutor(OKXConfig(profile=profile, demo=demo))
    return _default_executor


def create_executor(config: OKXConfig) -> OKXExecutor:
    """创建新执行器实例"""
    return OKXExecutor(config)