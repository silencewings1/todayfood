"""FastAPI 应用入口

启动方式：
    cd backend
    source ~/.py_food/bin/activate
    uvicorn app.main:app --reload --port 8000

或：
    python -m app.main

文档：http://localhost:8000/docs
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

# 把项目根目录加入 sys.path，让 admin.backend 包可被导入
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.fortune import router as fortune_router
from app.api.meta import router as meta_router
from app.config import settings
from app.services.scheduler import daily_refresh_task

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
PROJECT_ROOT = _PROJECT_ROOT
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
ADMIN_FRONTEND = PROJECT_ROOT / "admin" / "frontend"


class ApiLogMiddleware:
    """旁路复制安全文本请求体，并记录业务 API 调用。"""

    _CAPTURE_TYPES = ("application/json", "application/x-www-form-urlencoded")

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if scope["type"] != "http" or not path.startswith("/api"):
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_type = headers.get(b"content-type", b"").decode("latin-1").lower()
        capture = (
            settings.admin.logs.capture_api_body
            and any(content_type.startswith(item) for item in self._CAPTURE_TYPES)
        )
        body_parts: list[bytes] = []
        body_limit = max(0, settings.admin.logs.api_body_max_chars) * 4
        status = 500
        start = time.perf_counter()

        async def receive_wrapper():
            message = await receive()
            if capture and message["type"] == "http.request" and body_limit:
                remaining = body_limit - sum(len(part) for part in body_parts)
                if remaining > 0:
                    body_parts.append(message.get("body", b"")[:remaining])
            return message

        async def send_wrapper(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        finally:
            cost_ms = (time.perf_counter() - start) * 1000
            method = scope.get("method", "")
            logger.info("%s %s -> %d (%.1fms)", method, path, status, cost_ms)
            try:
                from admin.backend.collector import log_api_call
                req_body = b"".join(body_parts).decode("utf-8", errors="replace") or None
                log_api_call(
                    method=method, path=path, status=status,
                    cost_ms=cost_ms, req_body=req_body,
                )
            except Exception as e:
                logger.debug("写入 admin 日志失败: %s", e)


def create_app() -> FastAPI:
    """构造 FastAPI 应用实例"""
    app = FastAPI(
        title="今日宜吃 / today food API",
        description=(
            "「今日宜吃 / today food」小程序后端 —— 每日食历 / 抽签推荐 / AI 自由文本解析。\n\n"
            "默认走本地兜底（DummyProvider），设置 `USE_AI=1` 启用 openai-agents SDK。"
        ),
        version="0.1.0",
    )

    # CORS：允许的前端来源（来自 config/app.toml [server].frontend_origins
    # 或环境变量 FRONTEND_ORIGIN，逗号分隔）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.frontend_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ApiLogMiddleware)

    # 路由注册
    app.include_router(meta_router)
    app.include_router(fortune_router)

    # admin 路由
    try:
        from admin.backend.router import router as admin_router
        app.include_router(admin_router)
    except Exception as e:
        logger.warning("admin 路由加载失败: %s", e)

    # admin 前端静态文件挂载
    if ADMIN_FRONTEND.exists():
        app.mount("/admin/static", StaticFiles(directory=str(ADMIN_FRONTEND)), name="admin-static")

        @app.get("/admin", include_in_schema=False)
        @app.get("/admin/", include_in_schema=False)
        def serve_admin():
            return FileResponse(str(ADMIN_FRONTEND / "index.html"))

    # 生产部署：后端直接托管 Vite 构建产物，开发环境无 dist 时跳过
    if FRONTEND_DIST.exists():
        assets_dir = FRONTEND_DIST / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def serve_frontend(full_path: str):
            target = FRONTEND_DIST / full_path
            if full_path and target.is_file():
                return FileResponse(target)
            return FileResponse(FRONTEND_DIST / "index.html")

    # 生命周期：启动时预热缓存 + 后台每日刷新任务
    @app.on_event("startup")
    def _on_startup() -> None:
        # 启动后台线程，内部会立即预热当日缓存
        daily_refresh_task.start()

    @app.on_event("shutdown")
    def _on_shutdown() -> None:
        daily_refresh_task.stop()

    logger.info("FastAPI 应用已创建，AI 启用状态: %s", settings.use_ai)

    # admin 凭证校验：未配置则警告（admin 路由仍可加载，但无法登录）
    admin_cfg = settings.admin
    if not admin_cfg.username or not admin_cfg.password:
        logger.warning(
            "admin 凭证未配置，后台管理无法登录。"
            "请通过环境变量 ADMIN_USERNAME / ADMIN_PASSWORD 注入（见 backend/.env.example）。"
        )

    return app


app = create_app()


def main() -> None:
    """本地启动入口：python -m app.main"""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
