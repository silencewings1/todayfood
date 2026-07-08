"""AI 菜品存储层

将 AI 选菜结果持久化到 SQLite，支持：
- save_food: 保存 AI 生成的菜品（title 唯一，重复时更新为最新记录）
- get_latest_food: 获取最近一条 AI 菜品（首页首次加载用）
- get_random_food: 随机取一条 AI 菜品（频率限制时用）
- get_food_by_title: 按菜名查菜品

复用 admin/backend/db.py 的 SQLite 连接（同一数据库 backend/data/log.db）。
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 复用同一数据库文件
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_DB_DIR = _BACKEND_ROOT / "data"
_DB_PATH = _DB_DIR / "log.db"

_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_food_table() -> None:
    """初始化 ai_foods 表（幂等）"""
    with _lock, _get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS ai_foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            food_data TEXT NOT NULL,
            date TEXT NOT NULL,
            created_ts REAL NOT NULL,
            updated_ts REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_ai_foods_date ON ai_foods(date);
        CREATE INDEX IF NOT EXISTS idx_ai_foods_ts ON ai_foods(updated_ts);
        """)


def save_food(food: dict, date_str: str) -> None:
    """保存 AI 菜品（title 重复时更新为最新记录）

    Args:
        food: 完整的 FoodItem dict
        date_str: 日期字符串 YYYY-MM-DD
    """
    title = food.get("title", "")
    if not title:
        return
    food_json = json.dumps(food, ensure_ascii=False)
    now = time.time()
    with _lock, _get_conn() as conn:
        conn.execute(
            "INSERT INTO ai_foods(title, food_data, date, created_ts, updated_ts) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(title) DO UPDATE SET "
            "food_data=excluded.food_data, date=excluded.date, updated_ts=excluded.updated_ts",
            (title, food_json, date_str, now, now),
        )


def get_latest_food() -> Optional[dict]:
    """获取最近一条 AI 菜品"""
    with _lock, _get_conn() as conn:
        row = conn.execute(
            "SELECT food_data FROM ai_foods ORDER BY updated_ts DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["food_data"])
    except (json.JSONDecodeError, KeyError):
        return None


def get_random_food(exclude_title: Optional[str] = None) -> Optional[dict]:
    """随机取一条 AI 菜品（可排除指定菜名）"""
    with _lock, _get_conn() as conn:
        if exclude_title:
            row = conn.execute(
                "SELECT food_data FROM ai_foods WHERE title != ? ORDER BY RANDOM() LIMIT 1",
                (exclude_title,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT food_data FROM ai_foods ORDER BY RANDOM() LIMIT 1"
            ).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["food_data"])
    except (json.JSONDecodeError, KeyError):
        return None


def get_food_by_title(title: str) -> Optional[dict]:
    """按菜名查菜品"""
    with _lock, _get_conn() as conn:
        row = conn.execute(
            "SELECT food_data FROM ai_foods WHERE title = ? LIMIT 1", (title,)
        ).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["food_data"])
    except (json.JSONDecodeError, KeyError):
        return None


def find_food_by_id(food_id: str) -> Optional[dict]:
    """按菜品 id 查找（扫描 DB，AI 菜品数量少无需索引）"""
    with _lock, _get_conn() as conn:
        rows = conn.execute("SELECT food_data FROM ai_foods").fetchall()
    for row in rows:
        try:
            food = json.loads(row["food_data"])
            if food.get("id") == food_id:
                return food
        except (json.JSONDecodeError, KeyError):
            continue
    return None


# 模块加载时初始化表
init_food_table()
