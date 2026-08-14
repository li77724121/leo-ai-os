#!/usr/bin/env python3
"""V21 PowerPM AI V3 - AI新能源项目操作系统"""
import json, os
from datetime import datetime

BASE = "/Users/leo/Desktop/leohermes"
POWERPM_DIR = f"{BASE}/powerpm_v3"
os.makedirs(POWERPM_DIR, exist_ok=True)

EUROPEAN_STANDARDS = {
    "germany": ["DIN VDE 0100", "DIN EN 61851", " Eichrecht"],
    "eu": ["EU Directive 2014/94", "AFIR Regulation", "CE Marking"],
    "netherlands": ["NEN 1010", "Netherlands Grid Code"],
}

class PowerPMV3:
    def __init__(self):
        self.db_file = f"{POWERPM_DIR}/projects.json"
    
    def generate_engineering_plan(self, project: dict) -> dict:
        power = project.get("power_kva", 0)
        plan = {
            "project": project.get("name", "未命名"),
            "power_kva": power,
            "recommended_equipment": [],
            "construction_phases": [],
            "risk_points": [],
            "cost_estimate_eur": 0,
            "european_standards": EUROPEAN_STANDARDS,
            "generated_at": datetime.now().isoformat()
        }
        
        if power <= 500:
            plan["recommended_equipment"] = ["60kW DC快充×2", "配电柜", "电缆"]
            plan["construction_phases"] = ["设计(7d)", "施工(14d)", "调试(3d)"]
            plan["cost_estimate_eur"] = 50000
        elif power <= 3000:
            plan["recommended_equipment"] = ["180kW DC快充×6", "变压器1000kVA", "配电系统", "监控系统"]
            plan["construction_phases"] = ["设计(14d)", "土建(21d)", "安装(21d)", "调试(7d)"]
            plan["cost_estimate_eur"] = 200000
        else:
            plan["recommended_equipment"] = ["350kW超充×10", "变压器2500kVA", "储能系统", "光伏顶棚"]
            plan["construction_phases"] = ["设计(30d)", "审批(60d)", "土建(45d)", "安装(30d)", "调试(14d)"]
            plan["cost_estimate_eur"] = 800000
        
        plan["risk_points"] = ["电网容量确认", "审批周期", "设备交货期"]
        
        with open(self.db_file, "a") as f:
            f.write(json.dumps(plan, ensure_ascii=False) + "\n")
        return plan
    
    def get_standards(self, country: str) -> list:
        return EUROPEAN_STANDARDS.get(country, [])

def format_plan(plan: dict) -> str:
    lines = [f"⚡ *工程方案: {plan['project']}*", f"容量: {plan['power_kva']}kVA\n"]
    lines.append("📋 设备清单:")
    for e in plan["recommended_equipment"]:
        lines.append(f"  • {e}")
    lines.append(f"\n📅 施工阶段:")
    for p in plan["construction_phases"]:
        lines.append(f"  • {p}")
    lines.append(f"\n💰 估算成本: €{plan['cost_estimate_eur']:,}")
    lines.append(f"\n📜 适用欧洲标准:")
    for country, standards in plan["european_standards"].items():
        for s in standards:
            lines.append(f"  • [{country.upper()}] {s}")
    return "\n".join(lines)

if __name__ == "__main__":
    pm = PowerPMV3()
    plan = pm.generate_engineering_plan({"name": "柏林充电站", "power_kva": 3000})
    print(format_plan(plan))
