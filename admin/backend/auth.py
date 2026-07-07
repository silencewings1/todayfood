"""账号密码鉴权

凭证从环境变量读取：ADMIN_USERNAME / ADMIN_PASSWORD
默认 admin / admin123（仅本地用，生产必须改）
"""
from __future__ import annotations

import os
import secrets
import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
SESSION_COOKIE = "admin_token"
SESSION_MAX_AGE = 86400  # 1 天


def login(username: str, password: str, response: Response) -> bool:
    """校验账号密码，成功则写 cookie 并返回 True"""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        token = secrets.token_urlsafe(32)
        from admin.backend import db
        db.create_session(token, SESSION_MAX_AGE)
        response.set_cookie(
            key=SESSION_COOKIE, value=token,
            max_age=SESSION_MAX_AGE, httponly=True, samesite="lax",
        )
        return True
    return False


def logout(request: Request, response: Response) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        from admin.backend import db
        db.delete_session(token)
    response.delete_cookie(SESSION_COOKIE)


def check_auth(request: Request) -> bool:
    """校验请求是否已登录"""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return False
    from admin.backend import db
    return db.check_session(token)


def unauthorized() -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": "未登录或会话过期"})
