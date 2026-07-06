"""食历相关请求/响应模型

字段命名与前端 useFortune.js 中的对象保持一致（驼峰），
便于前端 fetch 后直接赋值给 state，无需字段映射。
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ===== 通用子结构 =====

class TodayInfo(BaseModel):
    """当日基础信息"""
    text: str = Field(..., description="2026 年 7 月 6 日 · 周一")
    short: str = Field(..., description="7 月 6 日")
    week: str = Field(..., description="一/二/.../日")
    seed: int = Field(..., description="日期种子 YYYYMMDD")
    date: str = Field(..., description="YYYY-MM-DD，后端新增便于缓存")


class LuckySet(BaseModel):
    """幸运三件套"""
    flavor: str
    color: str
    direction: str


class SignObj(BaseModel):
    """签文对象"""
    name: str
    level: str
    text: str


class FoodItem(BaseModel):
    """菜品完整对象（与前端 foodPool 项字段一致）"""
    id: str
    title: str
    category: str
    tags: dict
    stars: list[int]
    reason: str
    sign: str
    signName: str
    level: str
    luckyFlavor: str
    luckyColor: str
    direction: str
    cookTime: str
    difficulty: str
    ingredients: list[str]
    steps: list[str]
    tip: str


# ===== 请求 =====

class DrawRequest(BaseModel):
    """POST /api/fortune/draw 请求体

    - excludeId: 当前菜品 id，确保新抽到的菜不与之重复
    - preferences: 用户偏好，note 为「想吃点啥」自由文本（AI 解析）
    """
    excludeId: Optional[str] = None
    preferences: Optional[dict] = Field(default_factory=dict)


# ===== 响应 =====

class DailyExtras(BaseModel):
    """「今日食历」卡内容（每日固定）

    所有字段仅依赖 today.seed，与"再开一签"切换 current 无关。
    """
    almanacYi: list[str]
    almanacJi: list[str]
    suitable: list[str]
    avoid: list[str]
    lucky: LuckySet
    signNo: int
    signName: str
    signLevel: str
    signText: str


class TodayResponse(BaseModel):
    """GET /api/fortune/today 响应

    返回「今日食历」+「今日菜品」。
    """
    today: TodayInfo
    todayFood: FoodItem
    extras: DailyExtras


class DrawResponse(BaseModel):
    """POST /api/fortune/draw 响应

    返回一道新抽到的菜品。reason 可被 AI 个性化覆盖。
    """
    food: FoodItem
    aiUsed: bool = Field(False, description="本次是否走了 AI 解析路径")
