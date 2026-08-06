#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 网络自愈守护 (WiFi Watchdog)
功能:
  1. 定期检测网络连通性 (网关 + 公网)
  2. 检测到断网时, 自动按优先级切换可用 WiFi
  3. 切换成功后验证, 记录日志, 可选 Telegram 通知
安全:
  - 使用 networksetup 标准命令, 密码由 macOS 钥匙串自动提供, 脚本不接触密码
  - 仅在连续 N 次检测失败时才切换, 避免误判
用法:
  python3 wifi_watchdog.py          # 单次检测
  python3 wifi_watchdog.py --loop   # 循环模式 (launchd 用)
"""
import os
import sys
import time
import json
import socket
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

# ==================== 配置 ====================
WIFI_IFACE = "en0"
CHECK_INTERVAL = 60          # 循环检测间隔 (秒)
FAIL_THRESHOLD = 2           # 连续失败 N 次才触发切换
GATEWAYS = ["192.168.0.1", "192.168.1.1", "192.168.110.1"]
PUBLIC_URLS = [
    "https://www.baidu.com",
    "https://www.okx.com/api/v5/public/time",
    "https://api.github.com",
]
LOG_FILE = Path.home() / "leo-ai-os" / "trading_bot" / "wifi_watchdog.log"

# 高优先级候选 (家庭/办公网络, 按偏好排序; 系统会从钥匙串自动取密码)
PREFERRED_SSIDS = [
    "lee-home-5G", "li 专用-5G", "LEE HOME-5G", "lee-home", "li 专用",
    "li-work-5G", "lee-work-5G", "lee WiFi-5G", "ASUS-LEE", "Redmi_lee5G",
]

# 需要密码且已保存的候选: 从系统首选列表动态获取 (前 15 个)
DYNAMIC_CANDIDATES = True
DYNAMIC_COUNT = 15


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def current_ssid():
    rc, out, _ = run(["networksetup", "-getairportnetwork", WIFI_IFACE])
    if rc == 0 and "Current Wi-Fi Network" in out:
        return out.split(":", 1)[1].strip()
    return None


def ping_gateway():
    for gw in GATEWAYS:
        rc, out, _ = run(["ping", "-c", "1", "-t", "2", gw], timeout=5)
        if rc == 0 and "1 packets received" in out:
            return True
    return False


def check_public():
    for url in PUBLIC_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as r:
                if r.status == 200:
                    return True
        except Exception:
            continue
    return False


def network_ok():
    """网络是否可用: 网关通 或 公网通"""
    g = ping_gateway()
    if g:
        return True
    return check_public()


def get_saved_ssids():
    """从系统获取已保存的 WiFi 列表"""
    rc, out, _ = run(["networksetup", "-listpreferredwirelessnetworks", WIFI_IFACE])
    ssids = []
    if rc == 0:
        for line in out.splitlines()[1:]:
            s = line.strip()
            if s:
                ssids.append(s)
    return ssids


def try_connect(ssid):
    """尝试连接指定 WiFi (密码由钥匙串自动提供)"""
    log(f"🔄 尝试连接: {ssid}")
    rc, out, err = run(["networksetup", "-setairportnetwork", WIFI_IFACE, ssid], timeout=25)
    if rc != 0:
        log(f"  ⚠️ 连接失败: {err[:100]}")
        return False
    # 等待 DHCP + 验证
    for i in range(3):
        time.sleep(5)
        if network_ok():
            cur = current_ssid()
            log(f"  ✅ 切换成功 → {cur}")
            return True
    log(f"  ⚠️ 已连接但网络不通: {ssid}")
    return False


def auto_switch():
    """断网时自动切换"""
    log("🚨 检测到网络异常, 开始自动切换...")
    current = current_ssid()

    # 1. 高优先级候选
    candidates = list(PREFERRED_SSIDS)

    # 2. 动态候选 (系统已保存的前 N 个)
    if DYNAMIC_CANDIDATES:
        saved = get_saved_ssids()
        for s in saved[:DYNAMIC_COUNT]:
            if s not in candidates:
                candidates.append(s)

    # 3. 去除当前 SSID 和重复
    candidates = [c for c in candidates if c and c != current]

    for ssid in candidates:
        if try_connect(ssid):
            return ssid

    log("❌ 所有候选网络均失败, 等待下轮重试")
    return None


def send_telegram(text):
    """发送 Telegram 通知 (尽力而为)"""
    try:
        env_file = Path.home() / ".hermes" / ".env"
        token = chat = None
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"')
                if line.startswith("TELEGRAM_HOME_CHANNEL="):
                    chat = line.split("=", 1)[1].strip().strip('"')
        if not token or not chat:
            return
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({"chat_id": chat, "text": text}).encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            r.read()
    except Exception:
        pass


def main():
    loop = "--loop" in sys.argv
    fail_count = 0
    last_switch = 0

    log("🌐 WiFi Watchdog 启动 (接口: %s)" % WIFI_IFACE)

    while True:
        ok = network_ok()
        if ok:
            if fail_count > 0:
                log(f"✅ 网络已恢复 (连续失败 {fail_count} 次后)")
            fail_count = 0
        else:
            fail_count += 1
            log(f"⚠️ 网络异常 #{fail_count} (连续失败 {fail_count}/{FAIL_THRESHOLD})")
            if fail_count >= FAIL_THRESHOLD:
                if time.time() - last_switch > 120:  # 切换冷却 2 分钟
                    ssid = auto_switch()
                    last_switch = time.time()
                    if ssid:
                        send_telegram(f"🌐 网络自愈: 已自动切换到 WiFi [{ssid}]")
                    else:
                        send_telegram("🌐 网络自愈: 所有 WiFi 均不可用, 请检查路由器")
                fail_count = 0

        if not loop:
            break
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
