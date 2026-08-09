import asyncio
import logging
from typing import List, Dict, Any, Optional
from monitor import OKXAlphaMonitor
from analyzer import AlphaAnalyzer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingStrategy:
    """
    交易策略基类
    """
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """
        评估当前行情是否触发买入信号
        :return: True if buy signal triggered, else False
        """
        raise NotImplementedError("Strategies must implement evaluate()")

class VolumeSpikeStrategy(TradingStrategy):
    """
    成交量激增策略：当成交量超过平均值的 N 倍时触发
    """
    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold

    def evaluate(self, data: Dict[str, Any]) -> bool:
        # 这里的 data 包含 current_vol 和 avg_vol
        current_vol = data.get('volume', 0)
        avg_vol = data.get('avg_vol', 0)
        if avg_vol > 0 and current_vol > avg_vol * self.threshold:
            return True
        return False

class AlphaEngine:
    """
    Alpha 捕捉引擎：协调监控、决策与执行
    """
    def __init__(self, symbols: List[str], strategies: List[TradingStrategy], api_key: str = None, secret: str = None, password: str = None):
        self.symbols = symbols
        self.strategies = strategies
        self.monitor = OKXAlphaMonitor(symbols=symbols)
        self.analyzer = AlphaAnalyzer()
        self.history = {symbol: [] for symbol in symbols}
        
        # 初始化交易接口
        self.exchange = self.monitor.exchange
        if api_key and secret and password:
            self.exchange.apiKey = api_key
            self.exchange.secret = secret
            self.exchange.password = password
            self.is_live = True
        else:
            self.is_live = False
            logger.warning("⚠️ API keys not provided. Running in SIMULATION mode.")

    async def run(self):
        logger.info("🚀 OKX Alpha Engine started. Hunting for Alpha...")
        try:
            while True:
                for symbol in self.symbols:
                    # 1. 获取实时行情
                    ticker_data = await self.monitor.fetch_ticker(symbol)
                    if not ticker_data:
                        continue
                    
                    # 2. 计算平均成交量 (用于策略评估)
                    vol_history = self.history[symbol]
                    avg_vol = sum(vol_history) / len(vol_history) if vol_history else 0
                    
                    # 构造评估数据
                    eval_data = {**ticker_data, "avg_vol": avg_vol}
                    
                    # 3. 策略评估 (量化因子)
                    quant_signal = any(strategy.evaluate(eval_data) for strategy in self.strategies)
                    
                    # 4. 社交信号分析 (AI 因子)
                    # 模拟获取该币种的最新社交信号
                    mock_social_signals = [
                        {"symbol": symbol, "text": f"{symbol} is pumping! Huge news coming!", "weight": 1.2},
                        {"symbol": symbol, "text": f"Strong buy signal for {symbol} on the 1h chart", "weight": 1.0}
                    ]
                    social_scores = await self.analyzer.aggregate_signals(mock_social_signals)
                    social_score = social_scores.get(symbol, 0)
                    social_signal = self.analyzer.is_alpha_triggered(symbol, social_score)
                    
                    # 5. 双因子共振校验 (Quant + Social)
                    if quant_signal and social_signal:
                        logger.warning(f"🔥 ALPHA RESONANCE: {symbol} | Quant: OK | Social: {social_score:.2f} | Price: {ticker_data['last']}")
                        await self.execute_trade(symbol, ticker_data['last'])
                    elif quant_signal:
                        logger.info(f"📈 Quant signal only for {symbol}, waiting for social confirmation...")
                    elif social_signal:
                        logger.info(f"💬 Social signal only for {symbol}, waiting for volume spike...")
                    
                    # 更新历史记录
                    vol_history.append(ticker_data['volume'])
                    if len(vol_history) > 10:
                        vol_history.pop(0)
                
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            logger.info("Engine stopped.")
        finally:
            await self.monitor.close()

    async def execute_trade(self, symbol: str, price: float):
        """
        执行交易逻辑：真实下单 + 动态风控
        """
        if not self.is_live:
            logger.info(f"[SIMULATION] Executing BUY order for {symbol} at {price}...")
            return

        try:
            logger.info(f"🚀 REAL TRADE: Placing BUY order for {symbol} at {price}...")
            # OKX spot 市价买单使用 quoteOrderQty，避免把 USDT 金额误当成币种数量。
            order = await self.exchange.create_order(symbol, 'market', 'buy', None, 10, {'quoteOrderQty': 10})
            logger.info(f"✅ Order placed successfully: {order.get('id')}")
        except Exception as e:
            logger.error(f"❌ Trade execution failed: {e}")

async def main():
    # 这里的 API Key 应该从环境变量或 .env 文件中读取
    import os
    api_key = os.getenv("OKX_API_KEY")
    secret = os.getenv("OKX_SECRET")
    password = os.getenv("OKX_PASSWORD")

    # 定义策略：使用成交量激增策略
    strategies = [VolumeSpikeStrategy(threshold=2.5)]
    engine = AlphaEngine(
        symbols=["BTC/USDT", "ETH/USDT", "SOL/USDT", "PEPE/USDT"], 
        strategies=strategies,
        api_key=api_key,
        secret=secret,
        password=password
    )
    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())