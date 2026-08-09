import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "leo_designer.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS artworks (
            id TEXT PRIMARY KEY,
            prompt TEXT,
            image_url TEXT,
            category TEXT DEFAULT 'ai_generated',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_artwork(id: str, prompt: str, image_url: str, category: str = "ai_generated"):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO artworks (id, prompt, image_url, category) VALUES (?, ?, ?, ?)",
        (id, prompt, image_url, category)
    )
    conn.commit()
    conn.close()

def get_artworks(limit: int = 50):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM artworks ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# 初始化
init_db()
