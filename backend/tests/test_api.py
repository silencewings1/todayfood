"""API 接口测试

使用 FastAPI TestClient，覆盖：
- GET  /api/fortune/today
- POST /api/fortune/draw
- /health 健康检查
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.cache import daily_cache

client = TestClient(app)


def setup_function():
    """每个测试前清空缓存，避免相互干扰"""
    daily_cache.clear()


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["ai_provider"] == "dummy"  # 默认未启用 AI


def test_get_today_fortune():
    resp = client.get("/api/fortune/today")
    assert resp.status_code == 200
    body = resp.json()

    # today 字段
    today = body["today"]
    assert today["seed"] > 20240000
    assert "周" in today["text"]

    # todayFood 字段
    food = body["todayFood"]
    assert food["id"]
    assert food["title"]
    assert food["tags"]
    assert isinstance(food["steps"], list) and len(food["steps"]) >= 3

    # extras 字段（每日固定）
    extras = body["extras"]
    assert 3 <= len(extras["almanacYi"]) <= 4
    assert 2 <= len(extras["almanacJi"]) <= 3
    assert len(extras["suitable"]) == 3
    assert 3 <= len(extras["avoid"]) <= 5
    assert extras["lucky"]["flavor"]
    assert 1 <= extras["signNo"] <= 99
    assert extras["signName"]


def test_today_fortune_cached():
    """同日多次请求应返回相同结果（缓存生效）"""
    r1 = client.get("/api/fortune/today").json()
    r2 = client.get("/api/fortune/today").json()
    assert r1["today"]["seed"] == r2["today"]["seed"]
    assert r1["todayFood"]["id"] == r2["todayFood"]["id"]
    assert r1["extras"] == r2["extras"]


def test_draw_no_preference():
    """无偏好时应随机抽一道菜"""
    resp = client.post("/api/fortune/draw", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["food"]["id"]
    assert body["aiUsed"] is False  # 默认未启用 AI


def test_draw_with_preference():
    """带偏好时应正常返回菜品"""
    resp = client.post(
        "/api/fortune/draw",
        json={
            "excludeId": "tomato-beef",
            "preferences": {"mood": "spicy", "flavor": "spicy", "note": ""},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["food"]["id"] != "tomato-beef"


def test_draw_excludes_current():
    """连续抽多次都不应返回 excludeId"""
    for _ in range(10):
        body = client.post(
            "/api/fortune/draw",
            json={"excludeId": "tomato-beef", "preferences": {}},
        ).json()
        assert body["food"]["id"] != "tomato-beef"


def test_draw_with_note_dummy():
    """note 非空但 AI 未启用时应走本地兜底，aiUsed=False"""
    body = client.post(
        "/api/fortune/draw",
        json={"preferences": {"note": "想吃热乎的汤面"}},
    ).json()
    assert body["food"]["id"]
    assert body["aiUsed"] is False
