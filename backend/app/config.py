"""全局配置

通过环境变量读取，所有项均有默认值，便于本地零配置启动。
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # ===== 服务 =====
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    # 前端地址（用于 CORS）
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # ===== 时区 =====
    # 食历按北京时间切换，所有日期计算使用此 zone
    timezone: str = os.getenv("TZ", "Asia/Shanghai")

    # ===== AI 接入 =====
    # 是否启用 AI（默认关闭，走 DummyProvider 占位实现）
    use_ai: bool = os.getenv("USE_AI", "0") == "1"
    # OpenAI / 兼容服务
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # ===== 缓存 =====
    # 每日食历内存缓存开关（生产可换 Redis）
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "1") == "1"


settings = Settings()
