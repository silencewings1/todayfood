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
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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

    # CORS：允许前端开发服务器访问
    origins = [
        settings.frontend_origin,                # 默认 http://localhost:5173
        "http://localhost:5174",                 # Vite 端口漂移兜底
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 请求日志中间件：每次 /api 请求都打印一行明显的日志，便于前端联调观察
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        # 跳过 /docs /openapi.json 等非业务请求，减少噪音
        path = request.url.path
        if not path.startswith("/api"):
            return await call_next(request)

        method = request.method
        client = request.client.host if request.client else "?"
        start = time.perf_counter()

        # POST 打印请求体（便于看到前端传了什么偏好）
        body_preview = ""
        if method == "POST":
            try:
                raw = await request.body()
                body_preview = raw.decode("utf-8")[:200]
            except Exception:
                body_preview = "<read failed>"

        response = await call_next(request)

        cost_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "👉 %s %s <- %s -> %d (%.1fms)%s",
            method, path, client, response.status_code, cost_ms,
            f" body={body_preview}" if body_preview else "",
        )
        return response

    # 路由注册
    app.include_router(meta_router)
    app.include_router(fortune_router)

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
