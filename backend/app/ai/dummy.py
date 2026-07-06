"""DummyProvider

不调用任何 AI 服务的占位实现，所有方法返回"未启用"结果。
作为默认 Provider，让后端在零配置下可启动、可测试。
"""
from __future__ import annotations

from typing import Optional

from app.ai.base import AIProvider, NoteParseResult


class DummyProvider(AIProvider):
    """默认占位 Provider

    - parse_note 返回 None，上层走本地 pick_by_tags 兜底
    - personalize_reason 返回 None，上层用原 food.reason
    - generate_sign 返回 None，上层用静态签池
    """

    @property
    def name(self) -> str:
        return "dummy"

    @property
    def enabled(self) -> bool:
        return False

    async def parse_note(self, note: str, *, today_seed: int = 0) -> NoteParseResult:
        return NoteParseResult(prefs=None, note_raw=note)

    async def personalize_reason(self, food: dict, prefs: dict, *, today_seed: int = 0) -> Optional[str]:
        return None

    async def generate_sign(self, *, today_seed: int = 0) -> Optional[dict]:
        return None
