"""账号密码鉴权

凭证与 session 参数从 config/app.toml [admin] 读取，
可被环境变量 ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_SESSION_COOKIE 等覆盖。
凭证必须通过环境变量或 .env 注入，代码与 toml 中不再提供默认值。"""
from __future__ import annotations

import secrets

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.config import settings


def login(username: str, password: str, response: Response) -> bool:
    """校验账号密码，成功则写 cookie 并返回 True"""
    cfg = settings.admin
    if not cfg.username or not cfg.password:
        return False
    if secrets.compare_digest(username, cfg.username) and secrets.compare_digest(password, cfg.password):
        token = secrets.token_urlsafe(32)
        from admin.backend import db
        db.create_session(token, cfg.session_max_age)
        response.set_cookie(
            key=cfg.session_cookie, value=token,
            max_age=cfg.session_max_age, httponly=True, samesite="lax",
        )
        return True
    return False


def logout(request: Request, response: Response) -> None:
    cfg = settings.admin
    token = request.cookies.get(cfg.session_cookie)
    if token:
        from admin.backend import db
        db.delete_session(token)
    response.delete_cookie(cfg.session_cookie)


def check_auth(request: Request) -> bool:
    """校验请求是否已登录"""
    cfg = settings.admin
    token = request.cookies.get(cfg.session_cookie)
    if not token:
        return False
    from admin.backend import db
    return db.check_session(token)


def unauthorized() -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": "未登录或会话过期"})
