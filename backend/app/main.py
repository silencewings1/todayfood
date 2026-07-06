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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.fortune import router as fortune_router
from app.api.meta import router as meta_router
from app.config import settings

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

    # 路由注册
    app.include_router(meta_router)
    app.include_router(fortune_router)

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
