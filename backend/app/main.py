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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
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


def create_app() -> FastAPI:
    """构造 FastAPI 应用实例"""
    app = FastAPI(
        title="今日宜吃 API",
        description=(
            "「今日宜吃」小程序后端 —— 每日食历 / 抽签推荐 / AI 自由文本解析。\n\n"
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

    # 请求日志中间件：每次 /api 请求都打印日志 + 写入 SQLite
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        path = request.url.path
        # 跳过非业务请求（docs/openapi/admin静态）
        if not path.startswith("/api") and not path.startswith("/admin/api"):
            return await call_next(request)

        method = request.method
        client = request.client.host if request.client else "?"
        ua = request.headers.get("user-agent", "")
        start = time.perf_counter()

        # POST 读取请求体（便于看到前端传了什么偏好）
        body_preview = ""
        if method == "POST":
            try:
                raw = await request.body()
                body_preview = raw.decode("utf-8")[:500]
                # 把 body 塞回 request，供下游使用
                request._body = raw
            except Exception:
                body_preview = "<read failed>"

        response = await call_next(request)

        cost_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "👉 %s %s <- %s -> %d (%.1fms)%s",
            method, path, client, response.status_code, cost_ms,
            f" body={body_preview[:200]}" if body_preview else "",
        )

        # 写入 SQLite（失败不影响主流程）
        try:
            from admin.backend.collector import log_api_call
            # 读取响应体摘要（仅对小响应安全）
            resp_summary = ""
            if hasattr(response, 'body') and response.body:
                try:
                    resp_summary = response.body.decode("utf-8")[:300]
                except Exception:
                    pass
            log_api_call(
                method=method, path=path, client=client,
                status=response.status_code, cost_ms=cost_ms,
                req_body=body_preview, resp_body=resp_summary, ua=ua,
            )
        except Exception as e:
            logger.debug("写入 admin 日志失败: %s", e)

        return response

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
