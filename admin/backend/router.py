"""admin 路由

提供：
- /admin/api/login   登录
- /admin/api/logout  登出
- /admin/api/status  系统状态（需登录）
- /admin/api/api-logs API 日志查询（需登录）
- /admin/api/ai-logs  AI 日志查询（需登录）
- /admin/api/clear    清空日志（需登录）
"""
from __future__ import annotations

import json
import os
from urllib.request import urlopen

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from admin.backend import auth, db
from app.config import settings

router = APIRouter(prefix="/admin/api", tags=["admin"])


# ===== 登录/登出 =====
class LoginReq(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(req: LoginReq):
    resp = JSONResponse({"ok": True})
    if not auth.login(req.username, req.password, resp):
        return JSONResponse(status_code=401, content={"detail": "账号或密码错误"})
    return resp


@router.post("/logout")
def logout(request: Request):
    resp = JSONResponse({"ok": True})
    auth.logout(request, resp)
    return resp


# ===== 鉴权依赖 =====
def require_auth(request: Request):
    if not auth.check_auth(request):
        raise HTTPException(status_code=401, detail="未登录或会话过期")


def _local_ai_config() -> dict:
    ai = settings.ai
    return {
        "enabled": ai.enabled,
        "provider": "openai-agents" if ai.enabled and ai.api_key else "dummy",
        "api_protocol": ai.api_protocol,
        "model": ai.model,
        "base_url": ai.base_url or "(OpenAI 官方)",
        "ai_timeout": ai.ai_timeout,
        "has_api_key": bool(ai.api_key),
        "agents": {
            name: {"enabled": cfg.enabled, "model": cfg.model or ai.model, "temperature": cfg.temperature}
            for name, cfg in ai.agents.items()
        },
    }


def _monitored_ai_config() -> dict:
    health_url = os.getenv("MONITORED_HEALTH_URL", "http://127.0.0.1:9081/health")
    try:
        with urlopen(health_url, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        ai_config = data.get("ai_config") or _local_ai_config()
        ai_config["provider"] = data.get("ai_provider", ai_config.get("provider", "dummy"))
        return ai_config
    except Exception:
        return _local_ai_config()


# ===== 系统状态 =====
@router.get("/status", dependencies=[Depends(require_auth)])
def status() -> dict:
    return {
        "stats": db.get_stats(),
        "ai_config": _monitored_ai_config(),
    }


# ===== API 日志 =====
@router.get("/api-logs", dependencies=[Depends(require_auth)])
def api_logs(page: int = 1, page_size: int = 10, path: str = "",
             method: str = "", status: str = "", keyword: str = "") -> dict:
    status_val = int(status) if status else 0
    return db.query_api_logs(page=page, page_size=page_size, path=path,
                             method=method, status=status_val, keyword=keyword)


# ===== AI 日志 =====
@router.get("/ai-logs", dependencies=[Depends(require_auth)])
def ai_logs(page: int = 1, page_size: int = 10, agent: str = "",
            success: str = "", fallback: str = "") -> dict:
    success_val = None if success == "" else (success == "1")
    fallback_val = None if fallback == "" else (fallback == "1")
    return db.query_ai_logs(page=page, page_size=page_size, agent=agent,
                            success=success_val, fallback=fallback_val)


# ===== 清空日志 =====
class ClearReq(BaseModel):
    table: str = "all"  # api / ai / all


@router.post("/clear", dependencies=[Depends(require_auth)])
def clear(req: ClearReq) -> dict:
    db.clear_logs(req.table)
    return {"ok": True}


# ===== 前端页面挂载 =====
# /admin 返回 index.html，由 main.py 通过 StaticFiles 挂载静态资源
