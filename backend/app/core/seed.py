"""日期与种子相关算法

与前端 useFortune.js 中的 todayInfo / seededRandom 保持一致。
"""
from __future__ import annotations

from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Callable

from app.core.lunar import lunar_date_text


def today_info(tz: str = "Asia/Shanghai") -> dict:
    """获取当日信息

    返回结构：
        {
          "text": "2026 年 7 月 8 日 · 周三",
          "short": "丙午年 甲午月 廿四",  # 农历干支日期
          "week": "三",
          "seed": 20260708,
          "date": "2026-07-08"
        }
    """
    now = datetime.now(ZoneInfo(tz))
    week_zh = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
    return {
        "text": f"{now.year} 年 {now.month} 月 {now.day} 日 · 周{week_zh}",
        "short": lunar_date_text(date(now.year, now.month, now.day)),
        "week": week_zh,
        "seed": now.year * 10000 + now.month * 100 + now.day,
        "date": f"{now.year:04d}-{now.month:02d}-{now.day:02d}",
    }


def seeded_random(seed: int) -> Callable[[], float]:
    """LCG 伪随机数生成器

    与前端 seededRandom 完全一致：
        s = (s * 9301 + 49297) % 233280
        return s / 233280
    """
    s = seed

    def _rand() -> float:
        nonlocal s
        s = (s * 9301 + 49297) % 233280
        return s / 233280

    return _rand


def pick_sign_no(seed: int) -> int:
    """抽签编号（1-99 之间，按种子稳定）

    与前端 pickSignNo 一致：
        1 + floor(((seed * 7) % 233280) / 233280 * 99)
    """
    return 1 + int(((seed * 7) % 233280) / 233280 * 99)
