from __future__ import annotations

import sqlite3
import time
from types import SimpleNamespace

from fastapi import Response
from fastapi.testclient import TestClient

from admin.backend import auth, collector, db
from app.services import food_store


def _food(food_id: str, title: str) -> dict:
    return {"id": food_id, "title": title}


def test_login_rejects_empty_config(monkeypatch):
    monkeypatch.setattr(
        auth,
        "settings",
        SimpleNamespace(admin=SimpleNamespace(username="", password="")),
    )

    assert auth.login("", "", Response()) is False


def test_login_accepts_configured_credentials(monkeypatch):
    cfg = SimpleNamespace(
        username="admin",
        password="secret",
        session_max_age=60,
        session_cookie="admin_token",
    )
    monkeypatch.setattr(auth, "settings", SimpleNamespace(admin=cfg))
    monkeypatch.setattr(db, "create_session", lambda token, max_age: None)

    response = Response()
    assert auth.login("admin", "secret", response) is True
    assert "admin_token=" in response.headers["set-cookie"]


def test_daily_food_keeps_first_value(tmp_path, monkeypatch):
    db_path = tmp_path / "food.db"
    monkeypatch.setattr(
        food_store, "settings", SimpleNamespace(database_path=str(db_path))
    )
    food_store.init_food_table()

    first = food_store.save_daily_food_if_absent(
        "2026-07-11", _food("first", "第一道菜")
    )
    second = food_store.save_daily_food_if_absent(
        "2026-07-11", _food("second", "第二道菜")
    )

    assert first == second
    assert food_store.get_daily_food("2026-07-11")["id"] == "first"


def _log_settings(db_path, **overrides):
    logs = {
        "query_days": 30,
        "query_max_rows": 10000,
        "capture_api_body": True,
        "capture_ai_content": True,
        "api_body_max_chars": 4096,
        "ai_prompt_max_chars": 12000,
        "ai_response_max_chars": 12000,
        "retention_days": 30,
        "retention_max_rows": 10000,
    }
    logs.update(overrides)
    return SimpleNamespace(
        database_path=str(db_path), admin=SimpleNamespace(logs=SimpleNamespace(**logs))
    )


def test_collectors_capture_redact_and_truncate(tmp_path, monkeypatch):
    db_path = tmp_path / "logs.db"
    cfg = _log_settings(
        db_path, api_body_max_chars=80, ai_prompt_max_chars=24,
        ai_response_max_chars=80,
    )
    monkeypatch.setattr(db, "settings", cfg)
    monkeypatch.setattr(collector, "settings", cfg)
    db.init_db()

    collector.log_api_call(
        method="POST", path="/api/fortune/draw", status=200, cost_ms=12.5,
        req_body={"note": "想吃面", "auth": {"access_token": "api-secret"}},
    )
    collector.log_ai_call(
        agent="food_picker",
        prompt="password=prompt-secret " + "很长的提示" * 10,
        response='{"authorization":"Bearer raw-secret","answer":"面"}',
        parsed={"result": {"token": "parsed-secret", "food": "面"}},
        error="ValueError: private detail", success=False,
    )

    with sqlite3.connect(db_path) as conn:
        api_row = conn.execute(
            "SELECT client, req_body, resp_summary, ua FROM api_logs"
        ).fetchone()
        ai_row = conn.execute(
            "SELECT prompt, response, parsed, error FROM ai_logs"
        ).fetchone()

    assert api_row[0] is None and api_row[2:] == (None, None)
    assert "api-secret" not in api_row[1]
    assert '"access_token":"[REDACTED]"' in api_row[1]
    assert len(ai_row[0]) == 24 and ai_row[0].endswith("...")
    assert "prompt-secret" not in ai_row[0]
    assert "raw-secret" not in ai_row[1]
    assert "parsed-secret" not in ai_row[2]
    assert ai_row[3] == "ValueError"


def test_collectors_respect_disabled_capture(tmp_path, monkeypatch):
    db_path = tmp_path / "disabled.db"
    cfg = _log_settings(db_path, capture_api_body=False, capture_ai_content=False)
    monkeypatch.setattr(db, "settings", cfg)
    monkeypatch.setattr(collector, "settings", cfg)
    db.init_db()

    collector.log_api_call(method="POST", path="/api/test", req_body={"value": "private"})
    collector.log_ai_call(agent="test", prompt="private", response="private", parsed={"x": 1})

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT req_body FROM api_logs").fetchone() == (None,)
        assert conn.execute("SELECT prompt, response, parsed FROM ai_logs").fetchone() == (None, None, None)


def test_cleanup_old_physically_removes_expired_and_excess_rows(tmp_path, monkeypatch):
    db_path = tmp_path / "cleanup.db"
    cfg = _log_settings(db_path, retention_days=30, retention_max_rows=2)
    monkeypatch.setattr(db, "settings", cfg)
    db.init_db()

    with sqlite3.connect(db_path) as conn:
        for index in range(4):
            ts = time.time() - 31 * 86400 if index == 0 else time.time() + index
            conn.execute(
                "INSERT INTO api_logs(ts, method, path) VALUES (?, 'GET', ?)",
                (ts, f"/api/{index}"),
            )
            conn.execute(
                "INSERT INTO ai_logs(ts, agent) VALUES (?, ?)", (ts, f"agent-{index}")
            )

    db.cleanup_old()

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT path FROM api_logs ORDER BY id").fetchall() == [
            ("/api/2",), ("/api/3",),
        ]
        assert conn.execute("SELECT agent FROM ai_logs ORDER BY id").fetchall() == [
            ("agent-2",), ("agent-3",),
        ]


def test_request_body_capture_does_not_consume_draw_payload(tmp_path, monkeypatch):
    from app import main

    db_path = tmp_path / "integration.db"
    cfg = _log_settings(db_path)
    monkeypatch.setattr(db, "settings", cfg)
    monkeypatch.setattr(collector, "settings", cfg)
    monkeypatch.setattr(main.daily_refresh_task, "start", lambda: None)
    monkeypatch.setattr(main.daily_refresh_task, "stop", lambda: None)
    db.init_db()

    with TestClient(main.create_app()) as client:
        response = client.post(
            "/api/fortune/draw",
            json={
                "excludeId": None,
                "preferences": {"mood": "warm", "flavor": "清淡", "note": "想喝汤"},
                "token": "request-secret",
            },
        )

    assert response.status_code == 200
    with sqlite3.connect(db_path) as conn:
        req_body = conn.execute(
            "SELECT req_body FROM api_logs WHERE path='/api/fortune/draw' ORDER BY id DESC"
        ).fetchone()[0]
    assert "想喝汤" in req_body
    assert "request-secret" not in req_body
    assert '"token":"[REDACTED]"' in req_body
