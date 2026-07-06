"""根健康检查 & 首页"""
from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.ai import get_ai_provider
from app.config import settings

router = APIRouter(tags=["meta"])


@router.get("/", summary="服务根路径")
def root() -> dict:
    return {
        "name": "今日宜吃 API",
        "version": __version__,
        "docs": "/docs",
        "ai_enabled": get_ai_provider().enabled,
    }


@router.get("/health", summary="健康检查")
def health() -> dict:
    return {
        "status": "ok",
        "ai_provider": get_ai_provider().name,
        "ai_enabled": get_ai_provider().enabled,
        "use_ai_config": settings.use_ai,
    }
