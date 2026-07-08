"""抽签选择器

纯函数集合，供服务层调用：
- pick_today_food   按日期种子挑今日固定菜品
- pick_any          完全随机挑一道（可排除指定 id）
- pick_suitable     选今日宜吃组
- pick_avoid        选今日忌吃清单
- pick_lucky        选今日幸运三件套
- pick_sign_obj     抽一支签
"""
from __future__ import annotations

import random
from typing import Optional

from app.core.seed import seeded_random
from app.data.foods import food_pool, Food
from app.data.signs import pick_sign, Sign
from app.data.suitable import suitable_pool
from app.data.avoids import avoid_pool


def pick_today_food(seed: int) -> Food:
    """按日期种子挑"今日固定"菜品（每天稳定）"""
    rand = seeded_random(seed)
    idx = int(rand() * len(food_pool))
    return food_pool[idx]


def pick_any(exclude_id: Optional[str] = None) -> Food:
    """完全随机挑一道菜（可排除指定 id）

    与前端 pickAny 一致：从排除指定菜品后的池中随机取一个。
    """
    pool = [f for f in food_pool if f["id"] != exclude_id] if exclude_id else food_pool
    return random.choice(pool)


def pick_suitable(seed: int) -> list[str]:
    """选今日宜吃组（3 条）

    与前端 pickSuitable 一致：
        rand = seededRandom(seed)
        suitablePool[floor(rand() * len)]
    """
    rand = seeded_random(seed)
    return suitable_pool[int(rand() * len(suitable_pool))]


def pick_avoid(seed: int) -> list[str]:
    """选今日忌吃清单（3-5 条）

    与前端 pickAvoid 一致：
        rand = seededRandom(seed + 17)
        count = 3 + floor(rand() * 2)
        shuffled = [...avoidPool].sort(() => rand() - 0.5)
        return shuffled.slice(0, count)
    """
    rand = seeded_random(seed + 17)
    count = 3 + int(rand() * 2)
    # 用 rand() 作为排序 key 实现可复现洗牌
    shuffled = sorted(avoid_pool, key=lambda _: rand())
    return shuffled[:count]


def pick_lucky(seed: int) -> dict:
    """选今日幸运三件套（口味 / 颜色 / 食神方位）

    与前端 pickLucky 一致：
        rand = seededRandom(seed + 31)
    """
    rand = seeded_random(seed + 31)
    flavors = ["微辣", "清淡", "酸甜", "奶香", "酱香", "麻辣", "酸辣", "原味", "咸鲜", "甘甜"]
    colors = ["暖橙", "正红", "薄荷绿", "麦黄", "米白", "姜黄", "焦糖", "番茄红"]
    directions = [
        "那家总排队的店",
        "楼下走两步那家",
        "常点的那家老店",
        "朋友推荐过的新店",
        "外卖好评榜首位",
        "出地铁左拐那家",
        "公司食堂三楼",
        "冰箱里剩下的菜",
        "巷口藏着的小摊",
        "家里的厨房"
    ]
    return {
        "flavor": flavors[int(rand() * len(flavors))],
        "color": colors[int(rand() * len(colors))],
        "direction": directions[int(rand() * len(directions))],
    }


def pick_sign_obj(seed: int) -> Sign:
    """抽一支签（返回 { name, level, text }）

    复用 data/signs.py 的 pick_sign，与前端 pickSignObj 行为一致。
    """
    return pick_sign(seed)
