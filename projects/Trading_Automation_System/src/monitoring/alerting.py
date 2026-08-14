"""
监控与告警模块
实时看板数据收集、Telegram 告警、复盘报告生成
"""

from __future__ import annotations
import logging
import time
import json
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
import statistics

from ..base import StrategyContext, AccountBalance, Position, Order, Trade, AlertLevel

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    GAUGE = "gauge"      # 瞬时值
    COUNTER = "counter"  # 累计值
    HISTOGRAM = "histogram"  # 分布


@dataclass
class Metric:
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str]
    timestamp: int


@dataclass
class AlertRule:
    name: str
    condition: str           # 表达式，如 "strategy.drawdown_pct > 0.08"
    level: AlertLevel
    channels: List[str]      # ["telegram", "email", "webhook"]
    cooldown_sec: int = 3600
    action: str = ""         # 触发动作: "stop_strategy", "reduce_position", ""
    enabled: bool = True


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, max_points: int = 10000):
        self.max_points = max_points
        self._metrics: Dict[str, List[Metric]] = {}
        self._lock = threading.Lock()
    
    def record(self, metric: Metric):
        with self._lock:
            if metric.name not in self._metrics:
                self._metrics[metric.name] = []
            self._metrics[metric.name].append(metric)
            if len(self._metrics[metric.name]) > self.max_points:
                self._metrics[metric.name] = self._metrics[metric.name][-self.max_points:]
    
    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        self.record(Metric(name, value, MetricType.GAUGE, labels or {}, int(time.time() * 1000)))
    
    def record_counter(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        self.record(Metric(name, value, MetricType.COUNTER, labels or {}, int(time.time() * 1000)))
    
    def get_latest(self, name: str, labels: Dict[str, str] = None) -> Optional[Metric]:
        with self._lock:
            if name not in self._metrics:
                return None
            metrics = self._metrics[name]
            if labels:
                for m in reversed(metrics):
                    if all(m.labels.get(k) == v for k, v in labels.items()):
                        return m
            return metrics[-1] if metrics else None
    
    def get_series(self, name: str, labels: Dict[str, str] = None, 
                   start_time: int = None, end_time: int = None) -> List[Metric]:
        with self._lock:
            if name not in self._metrics:
                return []
            metrics = self._metrics[name]
            if labels:
                metrics = [m for m in metrics if all(m.labels.get(k) == v for k, v in labels.items())]
            if start_time:
                metrics = [m for m in metrics if m.timestamp >= start_time]
            if end_time:
                metrics = [m for m in metrics if m.timestamp <= end_time]
            return metrics
    
    def get_all_latest(self) -> Dict[str, Metric]:
        with self._lock:
            return {name: metrics[-1] for name, metrics in self._metrics.items() if metrics}


class AlertEngine:
    """告警引擎"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.rules: List[AlertRule] = []
        self._last_fired: Dict[str, float] = {}  # rule_name -> timestamp
        self._handlers: Dict[str, Callable] = {}
        self._lock = threading.Lock()
    
    def add_rule(self, rule: AlertRule):
        with self._lock:
            self.rules.append(rule)
    
    def remove_rule(self, name: str):
        with self._lock:
            self.rules = [r for r in self.rules if r.name != name]
    
    def register_handler(self, channel: str, handler: Callable[[AlertRule, Dict], None]):
        """注册告警通道处理器"""
        self._handlers[channel] = handler
    
    def evaluate(self, context: Dict[str, Any]):
        """评估所有规则"""
        with self._lock:
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                # 冷却检查
                last = self._last_fired.get(rule.name, 0)
                if time.time() - last < rule.cooldown_sec:
                    continue
                
                # 评估条件
                try:
                    triggered = self._eval_condition(rule.condition, context)
                except Exception as e:
                    logger.error(f"Alert rule '{rule.name}' eval error: {e}")
                    continue
                
                if triggered:
                    self._fire_alert(rule, context)
                    self._last_fired[rule.name] = time.time()
    
    def _eval_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """安全评估条件表达式"""
        # 简单的表达式求值，仅支持比较运算
        # 实际生产建议用 expr-lang 或类似库
        allowed_names = {k: v for k, v in context.items() if not k.startswith('_')}
        allowed_names.update({
            'true': True, 'false': False, 'none': None,
            'abs': abs, 'min': min, 'max': max, 'round': round
        })
        return eval(condition, {"__builtins__": {}}, allowed_names)
    
    def _fire_alert(self, rule: AlertRule, context: Dict[str, Any]):
        """触发告警"""
        alert_data = {
            "rule": rule.name,
            "level": rule.level.value,
            "message": f"Alert: {rule.name} - {rule.condition}",
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": rule.action
        }
        
        logger.warning(f"ALERT [{rule.level.value}] {rule.name}: {rule.condition}")
        
        for channel in rule.channels:
            handler = self._handlers.get(channel)
            if handler:
                try:
                    handler(rule, alert_data)
                except Exception as e:
                    logger.error(f"Alert handler '{channel}' error: {e}")
            else:
                logger.warning(f"No handler for alert channel: {channel}")
        
        # 执行动作
        if rule.action:
            self._execute_action(rule.action, context)
    
    def _execute_action(self, action: str, context: Dict[str, Any]):
        """执行告警动作"""
        logger.info(f"Executing alert action: {action}")
        # 实际动作由外部系统处理（如策略引擎监听）


class DashboardDataProvider:
    """看板数据提供者 - 聚合各类实时指标"""
    
    def __init__(self, metrics: MetricsCollector):
        self.metrics = metrics
    
    def get_dashboard_snapshot(self) -> Dict[str, Any]:
        """获取看板快照数据"""
        latest = self.metrics.get_all_latest()
        
        # 整理为看板友好格式
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "account": self._extract_account_metrics(latest),
            "strategies": self._extract_strategy_metrics(latest),
            "positions": self._extract_position_metrics(latest),
            "orders": self._extract_order_metrics(latest),
            "risk": self._extract_risk_metrics(latest),
            "system": self._extract_system_metrics(latest),
        }
    
    def _extract_account_metrics(self, latest: Dict[str, Metric]) -> Dict[str, Any]:
        return {
            "total_eq": self._get(latest, "account.total_eq"),
            "available_eq": self._get(latest, "account.available_eq"),
            "margin_ratio": self._get(latest, "account.margin_ratio"),
            "daily_pnl": self._get(latest, "account.daily_pnl"),
            "daily_pnl_pct": self._get(latest, "account.daily_pnl_pct"),
        }
    
    def _extract_strategy_metrics(self, latest: Dict[str, Metric]) -> List[Dict]:
        strategies = {}
        for name, metric in latest.items():
            if name.startswith("strategy."):
                parts = name.split(".")
                if len(parts) >= 3:
                    sid = parts[1]
                    mname = ".".join(parts[2:])
                    if sid not in strategies:
                        strategies[sid] = {"strategy_id": sid}
                    strategies[sid][mname] = metric.value
        return list(strategies.values())
    
    def _extract_position_metrics(self, latest: Dict[str, Metric]) -> List[Dict]:
        positions = {}
        for name, metric in latest.items():
            if name.startswith("position."):
                parts = name.split(".")
                if len(parts) >= 3:
                    inst = parts[1]
                    mname = ".".join(parts[2:])
                    if inst not in positions:
                        positions[inst] = {"inst_id": inst}
                    positions[inst][mname] = metric.value
        return list(positions.values())
    
    def _extract_order_metrics(self, latest: Dict[str, Metric]) -> Dict[str, Any]:
        return {
            "open_orders": self._get(latest, "orders.open_count"),
            "pending_orders": self._get(latest, "orders.pending_count"),
            "filled_today": self._get(latest, "orders.filled_today"),
            "rejected_today": self._get(latest, "orders.rejected_today"),
        }
    
    def _extract_risk_metrics(self, latest: Dict[str, Metric]) -> Dict[str, Any]:
        return {
            "max_drawdown": self._get(latest, "risk.max_drawdown"),
            "current_drawdown": self._get(latest, "risk.current_drawdown"),
            "total_exposure": self._get(latest, "risk.total_exposure"),
            "leverage": self._get(latest, "risk.leverage"),
            "margin_ratio": self._get(latest, "risk.margin_ratio"),
            "correlation_risk": self._get(latest, "risk.correlation_risk"),
        }
    
    def _extract_system_metrics(self, latest: Dict[str, Metric]) -> Dict[str, Any]:
        return {
            "api_latency_ms": self._get(latest, "system.api_latency_ms"),
            "api_error_rate": self._get(latest, "system.api_error_rate"),
            "data_freshness_sec": self._get(latest, "system.data_freshness_sec"),
            "uptime_sec": self._get(latest, "system.uptime_sec"),
        }
    
    def _get(self, latest: Dict[str, Metric], name: str, default: Any = 0) -> Any:
        m = latest.get(name)
        return m.value if m else default


class ReviewEngine:
    """复盘报告生成引擎"""
    
    def __init__(self, state_store, metrics: MetricsCollector):
        self.store = state_store
        self.metrics = metrics
    
    def generate_daily_report(self, run_id: str, date: datetime = None) -> Dict[str, Any]:
        """生成日报"""
        date = date or datetime.now(timezone.utc)
        start = int(date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        end = int((date + timedelta(days=1)).timestamp() * 1000)
        
        # 从数据库获取数据
        trades = self.store.get_trades(run_id=run_id, start_time=start, end_time=end)
        orders = self.store.get_orders(run_id=run_id)
        
        # 计算指标
        total_pnl = sum(t.px * t.sz * (1 if t.side.value == "sell" else -1) - t.fee for t in trades)
        trade_count = len(trades)
        win_trades = [t for t in trades if (t.side.value == "sell" and t.px > 0) or (t.side.value == "buy" and t.px < 0)]  # 简化
        win_count = len(win_trades)
        
        # 账户快照
        # TODO: 获取当日首尾快照计算收益率
        
        return {
            "report_type": "daily",
            "date": date.date().isoformat(),
            "run_id": run_id,
            "summary": {
                "total_pnl": total_pnl,
                "trade_count": trade_count,
                "win_count": win_count,
                "win_rate": win_count / trade_count if trade_count > 0 else 0,
                "total_fee": sum(t.fee for t in trades),
            },
            "trades": [asdict(t) for t in trades],
            "orders": [asdict(o) for o in orders if start <= o.c_time <= end],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def generate_weekly_report(self, run_id: str, week_start: datetime = None) -> Dict[str, Any]:
        """生成周报"""
        # 汇总 7 个日报
        week_start = week_start or datetime.now(timezone.utc) - timedelta(days=7)
        daily_reports = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            daily_reports.append(self.generate_daily_report(run_id, day))
        
        # 归因分析
        all_trades = []
        for r in daily_reports:
            all_trades.extend(r["trades"])
        
        # 按品种分组
        by_instrument = {}
        for t in all_trades:
            inst = t["inst_id"]
            if inst not in by_instrument:
                by_instrument[inst] = {"trades": 0, "pnl": 0, "volume": 0}
            by_instrument[inst]["trades"] += 1
            by_instrument[inst]["volume"] += t["sz"] * t["px"]
        
        return {
            "report_type": "weekly",
            "week_start": week_start.date().isoformat(),
            "run_id": run_id,
            "daily_summaries": [r["summary"] for r in daily_reports],
            "by_instrument": by_instrument,
            "total_pnl": sum(r["summary"]["total_pnl"] for r in daily_reports),
            "total_trades": sum(r["summary"]["trade_count"] for r in daily_reports),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def generate_monthly_report(self, run_id: str, month_start: datetime = None) -> Dict[str, Any]:
        """生成月报"""
        month_start = month_start or datetime.now(timezone.utc).replace(day=1)
        # TODO: 实现月报逻辑
        return {"report_type": "monthly", "run_id": run_id, "generated_at": datetime.now(timezone.utc).isoformat()}


# Telegram 告警处理器示例
def create_telegram_handler(bot_token: str, chat_id: str):
    """创建 Telegram 告警处理器"""
    import requests
    
    def handler(rule: AlertRule, alert_data: Dict):
        msg = (
            f"🚨 <b>[{alert_data['level'].upper()}]</b> {rule.name}\n"
            f"Condition: <code>{rule.condition}</code>\n"
            f"Time: {alert_data['timestamp']}\n"
            f"Action: {rule.action or 'None'}"
        )
        try:
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"},
                timeout=10
            )
        except Exception as e:
            logger.error(f"Telegram alert send failed: {e}")
    
    return handler


# 全局实例
_metrics_collector: Optional[MetricsCollector] = None
_alert_engine: Optional[AlertEngine] = None

def get_metrics_collector() -> MetricsCollector:
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

def get_alert_engine() -> AlertEngine:
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine(get_metrics_collector())
    return _alert_engine