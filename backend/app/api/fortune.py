"""食历相关 API

实现 TASKS.md 中的两个核心接口：
- GET  /api/fortune/today  自动任务（页面加载）—— 今日食历包 + 今日菜品
- POST /api/fortune/draw   按钮触发（再开一签 / 选一餐）—— 抽一道新菜
"""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.fortune import DrawRequest, DrawResponse, TodayResponse
from app.services.fortune_service import draw_food, get_today_fortune

router = APIRouter(prefix="/api/fortune", tags=["fortune"])


@router.get("/today", response_model=TodayResponse, summary="获取今日食历")
def get_today() -> TodayResponse:
    """今日食历 + 今日菜品

    - 所有用户同一天看到相同内容
    - 服务端按日期缓存，凌晨 0 点切换日期自动刷新
    """
    return get_today_fortune()


@router.post("/draw", response_model=DrawResponse, summary="抽一道新菜")
async def draw(req: DrawRequest) -> DrawResponse:
    """再开一签 / 选一餐

    - 入参：excludeId（当前菜品 id，避免重复）、preferences（mood/flavor/note）
    - note 非空且 AI 启用时，会调用 AI1 解析为结构化偏好
    - 返回：一道新菜品，aiUsed 标识是否走了 AI 路径
    """
    return await draw_food(req.excludeId, req.preferences)
