"""AI Provider 工厂

根据配置返回合适的 AIProvider 实例：
- USE_AI=1 且 OPENAI_API_KEY 已配置 -> OpenAIAgentsProvider
- 否则 -> DummyProvider（零配置可用，所有 AI 调用直接返回"未启用"）

默认行为（ai.toml 中 enabled=true）：
- 有 OPENAI_API_KEY -> 走 AI，AI 异常/超时由 Provider 内部回退本地
- 无 OPENAI_API_KEY -> 日志警告 + 回退 Dummy，保证服务可用
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

    首次调用时根据 settings.ai 决定实例化哪个 Provider。
    使用 lru_cache 保证全局单例。

    决策逻辑：
    1. ai.enabled=false -> DummyProvider
    2. ai.enabled=true 但 api_key 为空 -> 警告 + DummyProvider
    3. ai.enabled=true 且有 api_key -> OpenAIAgentsProvider
       （Provider 内部对每次调用做超时/异常兜底，失败回退本地）
    """
    ai = settings.ai

    if not ai.enabled:
        logger.info("AI 未启用（ai.enabled=false），使用 DummyProvider")
        return DummyProvider()

    if not ai.api_key:
        logger.warning(
            "AI 已启用但 OPENAI_API_KEY 未配置，回退 DummyProvider。"
            "配置 OPENAI_API_KEY 环境变量后即可启用 AI。"
        )
        return DummyProvider()

    # 启用 AI：尝试加载 OpenAIAgentsProvider
    try:
        from app.ai.openai_agents_provider import OpenAIAgentsProvider
        provider = OpenAIAgentsProvider()
        logger.info(
            "AI 已启用，使用 OpenAIAgentsProvider（protocol=%s, model=%s, ai_timeout=%ss）",
            ai.api_protocol, ai.model, ai.ai_timeout,
        )
        return provider
    except Exception as e:
        logger.warning("AI Provider 加载失败，回退 DummyProvider: %s", e)
        return DummyProvider()
