"""SQLite 访问层

表结构：
- api_logs: API 调用日志
- ai_logs: AI 模型调用日志
- admin_sessions: 登录 session

存储路径：backend/data/log.db（data/ 已加入 .gitignore）

查询参数（query_days / query_max_rows）从 config/app.toml [admin.logs] 读取，
可由环境变量 ADMIN_LOG_QUERY_DAYS / ADMIN_LOG_MAX_ROWS 覆盖。
"""
from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional

from app.config import settings

# backend/data/log.db
_BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
_DB_DIR = _BACKEND_ROOT / "data"
_DB_PATH = _DB_DIR / "log.db"

# 查询参数来自配置；用函数读取保证热加载生效
def _query_days() -> int:
    return settings.admin.logs.query_days


def _query_max_rows() -> int:
    return settings.admin.logs.query_max_rows


_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    """获取 SQLite 连接（线程安全）

    check_same_thread=False 允许多线程写入；
    实际写入由 _lock 串行化。
    """
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # 提升并发写性能
    return conn


def init_db() -> None:
    """初始化表结构（幂等）"""
    with _lock, _get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,              -- 时间戳
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            client TEXT,
            status INTEGER,
            cost_ms REAL,
            req_body TEXT,
            resp_summary TEXT,
            ua TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_api_ts ON api_logs(ts);
        CREATE INDEX IF NOT EXISTS idx_api_path ON api_logs(path);

        CREATE TABLE IF NOT EXISTS ai_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            agent TEXT NOT NULL,           -- note_parser / reason_writer / sign_generator
            prompt TEXT,
            response TEXT,
            parsed TEXT,                   -- 解析后结果 JSON
            cost_ms REAL,
            success INTEGER,               -- 0/1
            fallback INTEGER,              -- 0/1 是否走兜底
            error TEXT,
            tokens INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_ai_ts ON ai_logs(ts);
        CREATE INDEX IF NOT EXISTS idx_ai_agent ON ai_logs(agent);

        CREATE TABLE IF NOT EXISTS admin_sessions (
            token TEXT PRIMARY KEY,
            created_ts REAL NOT NULL,
            expire_ts REAL NOT NULL
        );
        """)


def insert_api_log(*, method: str, path: str, client: str = "", status: int = 0,
                   cost_ms: float = 0, req_body: str = "", resp_summary: str = "",
                   ua: str = "") -> None:
    with _lock, _get_conn() as conn:
        conn.execute(
            "INSERT INTO api_logs(ts, method, path, client, status, cost_ms, req_body, resp_summary, ua) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (time.time(), method, path, client, status, cost_ms, req_body, resp_summary, ua),
        )


def insert_ai_log(*, agent: str, prompt: str = "", response: str = "", parsed: str = "",
                  cost_ms: float = 0, success: bool = True, fallback: bool = False,
                  error: str = "", tokens: int = 0) -> None:
    with _lock, _get_conn() as conn:
        conn.execute(
            "INSERT INTO ai_logs(ts, agent, prompt, response, parsed, cost_ms, success, fallback, error, tokens) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (time.time(), agent, prompt, response, parsed, cost_ms,
             1 if success else 0, 1 if fallback else 0, error, tokens),
        )


def query_api_logs(*, page: int = 1, page_size: int = 50,
                   path: str = "", method: str = "", status: int = 0,
                   keyword: str = "") -> dict[str, Any]:
    """分页查询 API 日志

    返回 {"items": [...], "total": N, "page": p, "page_size": s}
    """
    cutoff = time.time() - _query_days() * 86400
    max_rows = _query_max_rows()
    where = ["ts >= ?", f"id IN (SELECT id FROM api_logs ORDER BY id DESC LIMIT {max_rows})"]
    params: list = [cutoff]
    if path:
        where.append("path LIKE ?")
        params.append(f"%{path}%")
    if method:
        where.append("method = ?")
        params.append(method)
    if status:
        where.append("status = ?")
        params.append(status)
    if keyword:
        where.append("(req_body LIKE ? OR resp_summary LIKE ? OR client LIKE ?)")
        params.extend([f"%{keyword}%"] * 3)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    offset = (page - 1) * page_size

    with _lock, _get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM api_logs {where_sql}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM api_logs {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def query_ai_logs(*, page: int = 1, page_size: int = 50,
                  agent: str = "", success: Optional[bool] = None,
                  fallback: Optional[bool] = None) -> dict[str, Any]:
    cutoff = time.time() - _query_days() * 86400
    max_rows = _query_max_rows()
    where = ["ts >= ?", f"id IN (SELECT id FROM ai_logs ORDER BY id DESC LIMIT {max_rows})"]
    params: list = [cutoff]
    if agent:
        where.append("agent = ?")
        params.append(agent)
    if success is not None:
        where.append("success = ?")
        params.append(1 if success else 0)
    if fallback is not None:
        where.append("fallback = ?")
        params.append(1 if fallback else 0)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    offset = (page - 1) * page_size

    with _lock, _get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM ai_logs {where_sql}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM ai_logs {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_stats() -> dict[str, Any]:
    """系统统计"""
    with _lock, _get_conn() as conn:
        api_total = conn.execute("SELECT COUNT(*) FROM api_logs").fetchone()[0]
        ai_total = conn.execute("SELECT COUNT(*) FROM ai_logs").fetchone()[0]
        ai_success = conn.execute("SELECT COUNT(*) FROM ai_logs WHERE success=1").fetchone()[0]
        ai_fallback = conn.execute("SELECT COUNT(*) FROM ai_logs WHERE fallback=1").fetchone()[0]
        avg_api_cost = conn.execute("SELECT AVG(cost_ms) FROM api_logs").fetchone()[0] or 0
        avg_ai_cost = conn.execute("SELECT AVG(cost_ms) FROM ai_logs").fetchone()[0] or 0
        # 最近 1 小时
        one_hour_ago = time.time() - 3600
        api_1h = conn.execute("SELECT COUNT(*) FROM api_logs WHERE ts>?", (one_hour_ago,)).fetchone()[0]
        ai_1h = conn.execute("SELECT COUNT(*) FROM ai_logs WHERE ts>?", (one_hour_ago,)).fetchone()[0]

    return {
        "api_total": api_total,
        "ai_total": ai_total,
        "ai_success_rate": (ai_success / ai_total * 100) if ai_total else 0,
        "ai_fallback_count": ai_fallback,
        "avg_api_cost_ms": round(avg_api_cost, 2),
        "avg_ai_cost_ms": round(avg_ai_cost, 2),
        "api_1h": api_1h,
        "ai_1h": ai_1h,
    }


def clear_logs(table: str = "all") -> None:
    """清空日志"""
    with _lock, _get_conn() as conn:
        if table in ("api", "all"):
            conn.execute("DELETE FROM api_logs")
        if table in ("ai", "all"):
            conn.execute("DELETE FROM ai_logs")


def cleanup_old(days: int = 7, max_rows: int = 10000) -> None:
    """物理删除旧日志；当前不由后台服务自动调用。"""
    cutoff = time.time() - days * 86400
    with _lock, _get_conn() as conn:
        conn.execute("DELETE FROM api_logs WHERE ts < ?", (cutoff,))
        conn.execute("DELETE FROM ai_logs WHERE ts < ?", (cutoff,))
        # 保留最新 max_rows 条
        conn.execute(
            "DELETE FROM api_logs WHERE id NOT IN "
            "(SELECT id FROM api_logs ORDER BY id DESC LIMIT ?)", (max_rows,)
        )
        conn.execute(
            "DELETE FROM ai_logs WHERE id NOT IN "
            "(SELECT id FROM ai_logs ORDER BY id DESC LIMIT ?)", (max_rows,)
        )


# ===== Session 管理 =====
def create_session(token: str, expire_seconds: int = 86400) -> None:
    now = time.time()
    with _lock, _get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO admin_sessions(token, created_ts, expire_ts) VALUES (?, ?, ?)",
            (token, now, now + expire_seconds),
        )


def check_session(token: str) -> bool:
    now = time.time()
    with _lock, _get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM admin_sessions WHERE token=? AND expire_ts>?", (token, now)
        ).fetchone()
        return row is not None


def delete_session(token: str) -> None:
    with _lock, _get_conn() as conn:
        conn.execute("DELETE FROM admin_sessions WHERE token=?", (token,))


# 模块加载时初始化表
init_db()
