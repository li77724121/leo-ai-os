import ccxt.async_support as ccxt
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OKXAlphaMonitor:
    """
    OKX Alpha Hunter - 行情监控原型
    """
    def __init__(self, symbols: List[str] = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]):
        self.symbols = symbols
        self.exchange = ccxt.okx()
        self.volume_threshold = 2.0  # 成交量激增阈值 (例如：当前成交量 > 平均成交量 * 2)

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取单个币种的实时行情"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                "symbol": symbol,
                "last": ticker['last'],
                "volume": ticker['baseVolume'],
                "change": ticker['percentage'],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}

    async def monitor_loop(self):
        """实时监控循环"""
        logger.info(f"Starting Alpha Monitor for symbols: {self.symbols}")
        
        # 存储历史成交量用于计算平均值
        history = {symbol: [] for symbol in self.symbols}
        
        try:
            while True:
                for symbol in self.symbols:
                    data = await self.fetch_ticker(symbol)
                    if not data:
                        continue
                    
                    current_vol = data['volume']
                    vol_history = history[symbol]
                    
                    if len(vol_history) > 0:
                        avg_vol = sum(vol_history) / len(vol_history)
                        if current_vol > avg_vol * self.volume_threshold:
                            logger.warning(f"🚨 ALPHA SIGNAL: {symbol} Volume Spike! Current: {current_vol:.2f}, Avg: {avg_vol:.2f}")
                    
                    # 更新历史记录 (保持最近 10 个采样点)
                    vol_history.append(current_vol)
                    if len(vol_history) > 10:
                        vol_history.pop(0)
                
                logger.info("Tick completed. Sleeping for 10s...")
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            logger.info("Monitor stopped.")
        finally:
            await self.exchange.close()

async def main():
    monitor = OKXAlphaMonitor()
    try:
        await monitor.monitor_loop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    asyncio.run(main())