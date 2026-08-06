#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💻 VS Code + Cline 采集器
检测 VS Code 进程/窗口 + Cline 任务状态
数据源:
  - ps 检测 Code 进程
  - ~/.cline/ 目录 (Cline 任务文件)
  - ~/Library/Application Support/Code/ (VS Code 状态)
"""
import json
import time
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import events
import state

INTERVAL = 20

CLINE_DIRS = [
    Path.home() / ".cline",
    Path.home() / ".config" / "cline",
    Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev",
]


def check_vscode_process():
    """检测 VS Code 是否运行 + 打开的窗口数"""
    try:
        r = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
        lines = r.stdout.splitlines()
        code_procs = [l for l in lines if "Visual Studio Code" in l and "Electron" in l]
        return len(code_procs) > 0, len(code_procs)
    except Exception:
        return False, 0


def find_cline_tasks():
    """查找 Cline 任务文件"""
    found = []
    for d in CLINE_DIRS:
        if d.exists():
            for f in d.rglob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8", errors="ignore"))
                    if isinstance(data, dict) and ("task" in data or "conversation" in data or "request" in data):
                        found.append({"path": str(f), "data": data})
                        break  # 每个目录取一个
                except Exception:
                    continue
    return found


def collect():
    running, win_count = check_vscode_process()

    data = {
        "editor": f"🟢 运行中 ({win_count}窗口)" if running else "⚪ 未打开",
        "cline": {"working": False, "task": "Cline: 空闲", "progress": 0, "detail": "无任务"},
        "files": [],
    }

    # Cline 任务
    tasks = find_cline_tasks()
    for t in tasks[:2]:
        d = t["data"]
        # 尝试找当前任务
        task_text = d.get("task") or d.get("conversation") or ""
        if task_text:
            data["cline"] = {
                "working": True,
                "task": f"Cline: {str(task_text)[:40]}",
                "progress": 50,
                "detail": f"模型: {d.get('model','?')} | 文件: {Path(t['path']).name}",
            }
            events.info("vscode", "task", f"Cline 任务: {str(task_text)[:40]}")
            break

    # 最近修改文件 (ops-dashboard 相关)
    try:
        r = subprocess.run(
            ["find", str(Path.home() / "leo-ai-os"), "-name", "*.py", "-mmin", "-30", "-type", "f"],
            capture_output=True, text=True, timeout=5)
        files = [f for f in r.stdout.splitlines() if f.strip()][:5]
        data["files"] = [f.split("/")[-1] for f in files]
    except Exception:
        pass

    state.update("vscode", data)


if __name__ == "__main__":
    while True:
        try:
            collect()
        except Exception as e:
            events.error("vscode", "system", f"VS Code采集失败: {e}")
        time.sleep(INTERVAL)
