"""AIProvider 抽象基类

定义所有 AI 接入点的方法签名与返回结构。
业务层通过此抽象调用 AI，不感知具体实现（Dummy / OpenAI Agents / 其他）。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NoteParseResult:
    """「想吃点啥」自由文本解析结果

    AI1 的输出：把"热乎的汤面"解析为结构化偏好，供 pick_by_tags 使用。
    若 AI 未能解析，应返回 prefs=None 让上层走兜底。
    """
    prefs: Optional[dict] = None
    """解析出的偏好，如 {"mood": "tired", "flavor": "light", "note_raw": "热乎的汤面"}"""

    note_raw: str = ""
    """原始 note 文本，回传便于日志/调试"""

    extra: dict = field(default_factory=dict)
    """AI 额外返回的字段（如解释、置信度等），便于扩展"""


class AIProvider(ABC):
    """AI 服务抽象接口

    所有方法均应：
    - 不抛异常（内部捕获，失败返回 None / 默认值）
    - 是协程（async），便于后端用 await 调用，统一异步模型
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 名称，便于日志/响应标识"""

    @property
    def enabled(self) -> bool:
        """是否真正启用 AI（Dummy 返回 False）"""
        return True

    @abstractmethod
    async def parse_note(self, note: str, *, today_seed: int = 0) -> NoteParseResult:
        """AI1: 解析「想吃点啥」自由文本为结构化偏好

        入参:
            note: 用户输入的自由文本，如"热乎的汤面"
            today_seed: 当日种子，可用于 prompt 上下文

        返回:
            NoteParseResult，prefs 为 None 表示解析失败
        """

    @abstractmethod
    async def personalize_reason(self, food: dict, prefs: dict, *, today_seed: int = 0) -> Optional[str]:
        """AI2: 生成个性化推荐理由

        入参:
            food: 菜品完整对象（dict 形式，便于序列化给 LLM）
            prefs: 用户偏好
            today_seed: 当日种子

        返回:
            个性化理由文本；None 表示放弃，上层用原 food.reason
        """

    @abstractmethod
    async def generate_sign(self, *, today_seed: int = 0) -> Optional[dict]:
        """AI3: 动态生成签文

        返回:
            {"name": str, "level": str, "text": str}；None 表示放弃，上层用静态签池
        """
