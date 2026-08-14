#!/usr/bin/env python3
"""V21 Strategy Simulator - AI战略模拟器"""
import json, os, random
from datetime import datetime, timedelta

BASE = "/Users/leo/Desktop/leohermes"
SIM_DIR = f"{BASE}/strategy_sim"
os.makedirs(SIM_DIR, exist_ok=True)

class StrategySimulator:
    def __init__(self):
        self.db_file = f"{SIM_DIR}/simulations.json"
    
    def simulate(self, market: str, budget_monthly: int, duration_months: int = 12) -> dict:
        base_score = {"Germany": 92, "Netherlands": 85, "Japan": 55, "China": 78}.get(market, 60)
        
        customers = int(base_score * duration_months * 0.1 + random.randint(-5, 10))
        mrr = customers * 199 * (base_score / 100)
        total_investment = budget_monthly * duration_months
        
        result = {
            "id": f"SIM{datetime.now().strftime('%Y%m%d%H%M')}",
            "market": market,
            "budget_monthly": budget_monthly,
            "duration_months": duration_months,
            "predicted_customers": max(customers, 5),
            "predicted_mrr": round(mrr, 2),
            "total_revenue": round(mrr * duration_months, 2),
            "total_cost": total_investment,
            "roi": round((mrr * duration_months - total_investment) / max(total_investment, 1) * 100, 1),
            "risk": "低" if base_score > 80 else "中" if base_score > 60 else "高",
            "timestamp": datetime.now().isoformat(),
            "confidence": min(base_score + random.randint(-5, 5), 99)
        }
        
        with open(self.db_file, "w") as f:
            json.dump([result], f, indent=2)
        return result

def format_simulation(sim: dict) -> str:
    emoji = "🟢" if sim["risk"] == "低" else "🟡" if sim["risk"] == "中" else "🔴"
    return (
        f"🎯 *战略模拟 - {sim['market']}*\n"
        f"投入: ${sim['budget_monthly']}/月 × {sim['duration_months']}月\n\n"
        f"📊 *预测*\n"
        f"客户: {sim['predicted_customers']}人\n"
        f"MRR: ${sim['predicted_mrr']:,.0f}/月\n"
        f"总收入: ${sim['total_revenue']:,.0f}\n"
        f"总成本: ${sim['total_cost']:,}\n"
        f"ROI: {sim['roi']}%\n\n"
        f"{emoji} 风险: {sim['risk']} | 置信度: {sim['confidence']}%"
    )

if __name__ == "__main__":
    sim = StrategySimulator()
    result = sim.simulate("Germany", 500, 12)
    print(format_simulation(result))
