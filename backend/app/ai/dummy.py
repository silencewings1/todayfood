"""Dummy Provider — AI 未启用时的占位实现

所有方法返回 None / 空结果，业务层自动走本地兜底。
"""
from __future__ import annotations

from typing import Optional

from app.ai.base import AIProvider


class DummyProvider(AIProvider):
    """未启用 AI 时的空实现"""

    @property
    def name(self) -> str:
        return "dummy"

    @property
    def enabled(self) -> bool:
        return False

    async def pick_food(self, context: dict, *, today_seed: int = 0) -> Optional[dict]:
        return None

    async def generate_sign(self, *, today_seed: int = 0) -> Optional[dict]:
        return None
