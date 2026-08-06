#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 极空间 Z2S 采集器 (syncthing API 方案)
极空间 App 已通过官方通道连接 NAS (127.0.0.1:13581 隧道)
本采集器读取本地 syncthing API (127.0.0.1:8384) 监控:
  - 极空间在线状态 (设备连接)
  - 同步进度/文件数
  - 最近同步活动

⚠️ SSH 深度采集 (CPU/Docker) 需极空间开启 SSH + 组网, 待后续
"""
import json
import time
import sys
import re
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import events
import state

INTERVAL = 30
SYNCTHING_API = "http://127.0.0.1:8384"
CONFIG_XML = Path.home() / "Library" / "Application Support" / "zspace" / "18577260181" / ".config" / "config.xml"


def get_api_key():
    """从 syncthing config.xml 提取 API key"""
    try:
        content = CONFIG_XML.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"<apikey>([^<]+)</apikey>", content)
        return m.group(1) if m else ""
    except Exception:
        return ""


def syncthing_get(path):
    key = get_api_key()
    if not key:
        return None
    try:
        req = urllib.request.Request(SYNCTHING_API + path, headers={"X-API-Key": key})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception:
        return None


def collect():
    # 1. 设备连接状态 (极空间在线?)
    conn = syncthing_get("/rest/system/connections")
    zspace_online = False
    zspace_addr = ""
    if conn:
        for dev_id, info in conn.get("connections", {}).items():
            if info.get("connected"):
                zspace_online = True
                zspace_addr = info.get("address", "")

    # 2. 同步文件夹状态
    folder_state = "unknown"
    global_files = local_files = 0
    synced = 0
    try:
        folders = syncthing_get("/rest/config/folders") or []
        for f in folders:
            fid = f.get("id", "")
            st = syncthing_get(f"/rest/db/status?folder={fid}")
            if st:
                folder_state = st.get("state", "unknown")
                global_files = st.get("globalFiles", 0)
                local_files = st.get("localFiles", 0)
                synced = st.get("needFiles", 0)
                break  # 只取第一个文件夹
    except Exception:
        pass

    data = {
        "status": "online" if zspace_online else "offline",
        "connected": zspace_online,
        "addr": zspace_addr,
        "sync_state": folder_state,
        "files": local_files,
        "global_files": global_files,
        "pending": synced,   # 待同步文件
        "method": "syncthing",
    }
    state.update("zspace", data)

    if zspace_online:
        events.success("zspace", "system",
                       f"极空间在线 (syncthing) | 同步: {folder_state} | 文件 {local_files}/{global_files} | 待同步 {synced}")
    else:
        events.warn("zspace", "network", "极空间 App 未连接 (syncthing 隧道断开)")


if __name__ == "__main__":
    while True:
        try:
            collect()
        except Exception as e:
            events.error("zspace", "system", f"极空间采集异常: {e}")
        time.sleep(INTERVAL)
