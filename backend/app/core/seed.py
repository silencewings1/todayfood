"""日期与种子相关算法

与前端 useFortune.js 中的 todayInfo / seededRandom 保持一致。
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Callable


def today_info(tz: str = "Asia/Shanghai") -> dict:
    """获取当日信息

    返回结构与前端 todayInfo() 一致：
        {
          "text": "2026 年 7 月 6 日 · 周一",
          "short": "7 月 6 日",
          "week": "一",
          "seed": 20260706,
          "date": "2026-07-06"   # 后端新增，便于缓存键
        }
    """
    now = datetime.now(ZoneInfo(tz))
    week_zh = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
    return {
        "text": f"{now.year} 年 {now.month} 月 {now.day} 日 · 周{week_zh}",
        "short": f"{now.month} 月 {now.day} 日",
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
