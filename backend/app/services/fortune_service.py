"""食历服务层

实现两个核心接口业务逻辑：
- get_today_fortune(): GET /api/fortune/today（页面首次加载）
- draw_food(): POST /api/fortune/draw（按钮触发：再开一签/选一餐）

设计要点：
1. 「今日食历」内容（黄历宜忌 + 干饭宜忌 + 幸运三件套 + 签文）仅依赖 today.seed，
   每日固定，对所有用户一致
2. 「今日菜品」首次加载时从数据库读取最近一条 AI 菜品，无则用静态池兜底
3. 「再开一签」优先调用 AI 选菜（含理由+做法+黄历结合），结果存入数据库
4. 频率限制：window_sec 秒内最多 max_calls 次 AI 调用，超限走数据库已有菜品
5. 当日食历结果按 date 缓存，避免重复计算
"""
from __future__ import annotations

import logging
from typing import Optional

from app.ai import get_ai_provider
from app.config import settings
from app.core.picker import (
    pick_any,
    pick_avoid,
    pick_by_tags,
    pick_lucky,
    pick_sign_obj,
    pick_suitable,
    pick_today_food,
)
from app.core.seed import pick_sign_no, today_info
from app.data.almanac import pick_almanac_ji, pick_almanac_yi
from app.schemas.fortune import (
    DailyExtras,
    DrawResponse,
    FoodItem,
    LuckySet,
    TodayInfo,
    TodayResponse,
)
from app.services.cache import daily_cache
from app.services.food_store import (
    get_latest_food,
    get_random_food,
    save_food,
)
from app.services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# 初始化频率限制器配置
rate_limiter.update_config(
    settings.rate_limit_window_sec,
    settings.rate_limit_max_calls,
)


def _build_daily_extras(seed: int) -> DailyExtras:
    """构造「今日食历」卡内容

    所有字段仅依赖 today.seed，每日固定不变。
    """
    sign = pick_sign_obj(seed)
    return DailyExtras(
        almanacYi=pick_almanac_yi(seed),
        almanacJi=pick_almanac_ji(seed),
        suitable=pick_suitable(seed),
        avoid=pick_avoid(seed),
        lucky=LuckySet(**pick_lucky(seed)),
        signNo=pick_sign_no(seed),
        signName=sign["name"],
        signLevel=sign["level"],
        signText=sign["text"],
    )


def _build_ai_context(today: dict, extras: DailyExtras, prefs: dict,
                      exclude_title: Optional[str] = None) -> dict:
    """构造 AI 选菜上下文（黄历 + 用户偏好）"""
    lucky = extras.lucky
    return {
        "date_text": today["text"],
        "lunar_text": today["short"],
        "almanac_yi": extras.almanacYi,
        "almanac_ji": extras.almanacJi,
        "lucky_flavor": lucky.flavor,
        "lucky_color": lucky.color,
        "lucky_direction": lucky.direction,
        "mood": prefs.get("mood"),
        "flavor": prefs.get("flavor"),
        "note": (prefs.get("note") or "").strip() or None,
        "exclude_title": exclude_title,
    }


def get_today_fortune() -> TodayResponse:
    """GET /api/fortune/today 业务实现

    返回「今日食历」+「今日菜品」，按 date 缓存。
    今日菜品优先从数据库加载最近一条 AI 菜品，无则用静态池。
    """
    today = today_info(settings.timezone)
    cache_key = f"today:{today['date']}"

    if settings.cache_enabled:
        cached = daily_cache.get(cache_key)
        if cached is not None:
            return cached

    extras = _build_daily_extras(today["seed"])

    # 优先从数据库加载最近一条 AI 菜品
    today_food = get_latest_food()
    if today_food is None:
        # 数据库为空，用静态池兜底
        today_food = pick_today_food(today["seed"])

    resp = TodayResponse(
        today=TodayInfo(**today),
        todayFood=FoodItem(**today_food),
        extras=extras,
    )

    if settings.cache_enabled:
        daily_cache.set(cache_key, resp)

    return resp


async def draw_food(
    exclude_id: Optional[str],
    preferences: Optional[dict],
) -> DrawResponse:
    """POST /api/fortune/draw 业务实现

    流程：
    1. 构造黄历上下文
    2. 检查频率限制
       - 未超限且 AI 启用 → 调用 AI pick_food（含理由+做法+黄历结合），存入数据库
       - 超限 → 从数据库随机取一道已有菜品
       - AI 失败 → 回退静态池
    3. 排除 exclude_id（若结果与之相同，强制重抽一个不同的）
    """
    prefs = preferences or {}
    today = today_info(settings.timezone)
    extras = _build_daily_extras(today["seed"])

    # 查当前菜品名（用于 AI 排除）
    exclude_title = None
    if exclude_id:
        # 从数据库或静态池查找当前菜品名
        from app.data.foods import food_pool
        for f in food_pool:
            if f["id"] == exclude_id:
                exclude_title = f["title"]
                break

    ai = get_ai_provider()
    ai_used = False
    rate_limited = False
    food_dict: Optional[dict] = None

    # 检查频率限制
    if ai.enabled and not rate_limiter.check():
        # 未超限，调用 AI 选菜
        context = _build_ai_context(today, extras, prefs, exclude_title)
        food_dict = await ai.pick_food(context, today_seed=today["seed"])
        if food_dict:
            # 保存到数据库（title 重复时更新为最新记录）
            save_food(food_dict, today["date"])
            # 清除今日缓存，使下次 GET /today 能加载到最新菜品
            daily_cache.clear()
            ai_used = True

    elif ai.enabled:
        # 频率超限，从数据库取已有菜品
        rate_limited = True
        logger.info("AI 选菜频率超限，从数据库取已有菜品")
        food_dict = get_random_food(exclude_title)

    # AI 失败或未启用或数据库也为空 → 静态池兜底
    if food_dict is None:
        food_dict = pick_any(exclude_id)

    return DrawResponse(
        food=FoodItem(**food_dict),
        aiUsed=ai_used,
        rateLimited=rate_limited,
    )
