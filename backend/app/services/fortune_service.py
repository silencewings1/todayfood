"""食历服务层

实现 TASKS.md 中的两个核心接口业务逻辑：
- get_today_fortune(): GET /api/fortune/today（自动任务 A1+A2）
- draw_food(): POST /api/fortune/draw（按钮触发：再开一签/选一餐）

设计要点：
1. 「今日食历」内容（黄历宜忌 + 干饭宜忌 + 幸运三件套 + 签文）仅依赖 today.seed，
   每日固定，对所有用户一致 —— 与前端修复后的 dailyExtras 行为对齐
2. 「今日菜品」也按 today.seed 稳定，作为页面首次加载默认推荐
3. 「再开一签」按用户偏好 + 当前时间盐抽新菜，不与 excludeId 重复
4. AI 接入点预留：draw_food 中当 preferences.note 非空时调用 AI 解析
5. 当日结果按 date 缓存，避免重复计算
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
    SignObj,
    TodayInfo,
    TodayResponse,
)
from app.services.cache import daily_cache

logger = logging.getLogger(__name__)


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


def get_today_fortune() -> TodayResponse:
    """GET /api/fortune/today 业务实现

    返回「今日食历」+「今日菜品」，按 date 缓存。
    """
    today = today_info(settings.timezone)
    cache_key = f"today:{today['date']}"

    if settings.cache_enabled:
        cached = daily_cache.get(cache_key)
        if cached is not None:
            return cached

    today_food = pick_today_food(today["seed"])
    extras = _build_daily_extras(today["seed"])

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
    1. 若 preferences.note 非空且 AI 启用 → 调用 AI1 解析 note 为结构化 prefs
       否则直接用 preferences 本身
    2. 若有任意偏好 → pick_by_tags 加权选菜
       否则 pick_any 完全随机
    3. 排除 exclude_id（若结果与之相同，强制重抽一个不同的）
    4. （可选）AI2 个性化 reason
    """
    prefs = preferences or {}
    today = today_info(settings.timezone)
    ai_used = False

    # AI1: note 解析
    note = (prefs.get("note") or "").strip()
    ai = get_ai_provider()
    if note and ai.enabled:
        parsed = await ai.parse_note(note, today_seed=today["seed"])
        if parsed.prefs:
            # 合并：AI 解析出的 mood/flavor 覆盖前端传入的（更准确）
            merged = dict(prefs)
            if parsed.prefs.get("mood"):
                merged["mood"] = parsed.prefs["mood"]
            if parsed.prefs.get("flavor"):
                merged["flavor"] = parsed.prefs["flavor"]
            merged["note"] = note
            merged["keywords"] = parsed.prefs.get("keywords", [])
            prefs = merged
            ai_used = True

    # 选菜
    have_any = any(v for k, v in prefs.items() if k in ("mood", "flavor"))
    if have_any:
        food = pick_by_tags(prefs, today_seed=today["seed"])
        # 兜底：与当前相同则随机一个不同的
        if exclude_id and food["id"] == exclude_id:
            food = pick_any(exclude_id)
    else:
        food = pick_any(exclude_id)

    # AI2: 个性化 reason（可选）
    food_dict = dict(food)
    if ai.enabled:
        new_reason = await ai.personalize_reason(food_dict, prefs, today_seed=today["seed"])
        if new_reason:
            food_dict["reason"] = new_reason
            ai_used = True

    return DrawResponse(food=FoodItem(**food_dict), aiUsed=ai_used)
