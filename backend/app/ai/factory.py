"""AI Provider 工厂

根据配置返回合适的 AIProvider 实例：
- 默认（USE_AI=0）: DummyProvider，零配置可用
- USE_AI=1: OpenAIAgentsProvider，依赖 openai-agents SDK + OPENAI_API_KEY

业务层通过 get_ai_provider() 获取单例，不感知具体实现。
"""
from __future__ import annotations

import logging
from functools import lru_cache

from app.ai.base import AIProvider
from app.ai.dummy import DummyProvider
from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_ai_provider() -> AIProvider:
    """获取 AI Provider 单例

    首次调用时根据 settings.use_ai 决定实例化哪个 Provider。
    使用 lru_cache 保证全局单例。
    """
    if not settings.use_ai:
        logger.info("AI 未启用（USE_AI=0），使用 DummyProvider")
        return DummyProvider()

    # 启用 AI：尝试加载 OpenAIAgentsProvider
    try:
        from app.ai.openai_agents_provider import OpenAIAgentsProvider
        provider = OpenAIAgentsProvider()
        logger.info("AI 已启用，使用 OpenAIAgentsProvider（model=%s）", settings.openai_model)
        return provider
    except Exception as e:
        logger.warning("AI Provider 加载失败，回退 DummyProvider: %s", e)
        return DummyProvider()
