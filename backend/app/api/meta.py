"""元信息 & 健康检查"""
from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.ai import get_ai_provider
from app.config import settings

router = APIRouter(tags=["meta"])


@router.get("/meta", summary="服务元信息")
def root() -> dict:
    return {
        "name": "今日宜吃 / today food API",
        "version": __version__,
        "docs": "/docs",
        "ai_enabled": get_ai_provider().enabled,
    }


@router.get("/health", summary="健康检查")
def health() -> dict:
    ai = settings.ai
    provider = get_ai_provider()
    return {
        "status": "ok",
        "ai_provider": provider.name,
        "ai_enabled": provider.enabled,
        "ai_config": {
            "enabled": ai.enabled,
            "api_protocol": ai.api_protocol,
            "model": ai.model,
            "base_url": ai.base_url or "(OpenAI 官方)",
            "ai_timeout": ai.ai_timeout,
            "has_api_key": bool(ai.api_key),
            "agents": {
                name: {"enabled": cfg.enabled, "model": cfg.model or ai.model, "temperature": cfg.temperature}
                for name, cfg in ai.agents.items()
            },
        },
    }
