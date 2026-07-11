"""食历服务层

两个核心接口：
- get_today_fortune(): GET /api/fortune/today（页面首次加载）
- draw_food(): POST /api/fortune/draw（按钮触发：再开一签/选一餐）

流程设计：
1. 首次加载 → 从数据库取最近一条 AI 菜品，DB 为空则静态池兜底
2. 按钮选菜 → 优先 AI pick_food（含理由+做法+黄历结合），结果存入 DB
3. 频率限制 → window_sec 秒内最多 max_calls 次 AI 调用，超限走 DB 已有菜品
4. 兜底 → AI 失败/未启用/DB 为空时，从静态池随机取
5. 签文 → AI 菜品无签文字段，用当日黄历签文补全
"""
from __future__ import annotations

import logging
from typing import Optional

from app.ai import get_ai_provider
from app.config import settings
from app.core.picker import (
    pick_any,
    pick_avoid,
    pick_lucky,
    pick_sign_obj,
    pick_suitable,
    pick_today_food,
)
from app.core.seed import pick_sign_no, today_info
from app.data.almanac import pick_almanac_ji, pick_almanac_yi
from app.data.foods import food_pool
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
    find_food_by_id,
    get_daily_food,
    get_random_food,
    save_daily_food_if_absent,
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
    """构造「今日食历」卡内容（每日固定，仅依赖 seed）"""
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


def _fill_sign_fields(food: dict, extras: DailyExtras) -> None:
    """用当日签文补全菜品的空签文字段（AI 菜品无签文，静态池已有则跳过）"""
    if not food.get("signName"):
        food["signName"] = extras.signName
    if not food.get("level"):
        food["level"] = extras.signLevel
    if not food.get("sign"):
        food["sign"] = extras.signText


def _lookup_exclude_title(exclude_id: Optional[str]) -> Optional[str]:
    """查找当前菜品名（先查静态池，再查 DB），用于告诉 AI 不要推荐相同的菜"""
    if not exclude_id:
        return None
    # 静态池
    for f in food_pool:
        if f["id"] == exclude_id:
            return f["title"]
    # AI 菜品数据库
    db_food = find_food_by_id(exclude_id)
    if db_food:
        return db_food.get("title")
    return None


def get_today_fortune() -> TodayResponse:
    """GET /api/fortune/today

    今日菜品按日期固定，用户抽菜不会改变首页结果。
    """
    today = today_info(settings.timezone)
    cache_key = f"today:{today['date']}"

    if settings.cache_enabled:
        cached = daily_cache.get(cache_key)
        if cached is not None:
            return cached

    extras = _build_daily_extras(today["seed"])

    today_food = get_daily_food(today["date"])
    if today_food is None:
        today_food = save_daily_food_if_absent(
            today["date"], pick_today_food(today["seed"]), "static"
        )

    _fill_sign_fields(today_food, extras)

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
    """POST /api/fortune/draw

    流程：
    1. 查当前菜品名（排除重复）
    2. 未超限+AI启用 → AI pick_food → 存 DB → 清缓存
    3. 超限 → 从 DB 随机取已有菜品
    4. 兜底 → 静态池 pick_any
    """
    prefs = preferences or {}
    today = today_info(settings.timezone)
    extras = _build_daily_extras(today["seed"])
    exclude_title = _lookup_exclude_title(exclude_id)

    ai = get_ai_provider()
    ai_used = False
    rate_limited = False
    food_dict: Optional[dict] = None

    if ai.enabled and not rate_limiter.check():
        # AI 选菜
        context = _build_ai_context(today, extras, prefs, exclude_title)
        food_dict = await ai.pick_food(context, today_seed=today["seed"])
        if food_dict:
            save_food(food_dict, today["date"])
            ai_used = True

    elif ai.enabled:
        # 频率超限，从 DB 取已有菜品
        rate_limited = True
        logger.info("AI 选菜频率超限，从数据库取已有菜品")
        food_dict = get_random_food(exclude_title)

    # 兜底：AI 失败/未启用/DB 为空
    if food_dict is None:
        food_dict = pick_any(exclude_id)

    _fill_sign_fields(food_dict, extras)

    return DrawResponse(
        food=FoodItem(**food_dict),
        aiUsed=ai_used,
        rateLimited=rate_limited,
    )
