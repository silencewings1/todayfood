"""AIProvider 抽象基类

定义 AI 接入点的方法签名与返回结构。
业务层通过此抽象调用 AI，不感知具体实现（Dummy / OpenAI Agents / 其他）。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


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
    async def pick_food(self, context: dict, *, today_seed: int = 0) -> Optional[dict]:
        """AI 选菜（含理由 + 做法 + 黄历结合）

        入参:
            context: 选菜上下文，包含：
                - date_text: 公历日期文本，如 "2026 年 7 月 8 日 · 周三"
                - lunar_text: 农历干支日期，如 "丙午年 甲午月 廿四"
                - almanac_yi: 黄历宜列表
                - almanac_ji: 黄历忌列表
                - lucky_flavor / lucky_color / lucky_direction: 幸运三件套
                - mood / flavor / note: 用户偏好
                - exclude_title: 当前菜品名（避免重复）
            today_seed: 当日种子

        返回:
            完整菜品 dict（字段同 FoodItem），None 表示放弃，上层走本地兜底
        """

    @abstractmethod
    async def generate_sign(self, *, today_seed: int = 0) -> Optional[dict]:
        """动态生成签文（可选功能，默认禁用）

        返回:
            {"name": str, "level": str, "text": str}；None 表示放弃，上层用静态签池
        """
