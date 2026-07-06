"""黄历宜忌数据池

从前端 src/data/almanac.js 迁移而来。
pick_almanac_yi / pick_almanac_ji 按 seed 稳定抽取。
"""
from __future__ import annotations

# 黄历"宜"项池（每日随机挑 3-4 条）
almanac_yi_pool: list[str] = [
    "祭祀", "祈福", "开光", "出行", "解除", "入宅", "移徙",
    "安床", "修造", "动土", "上梁", "开市", "交易", "立券",
    "挂匾", "纳财", "栽种", "纳畜", "启钻", "拆卸", "伐木",
    "经络", "酝酿", "理发", "整手足甲", "冠笄", "会亲友",
    "进人口", "裁衣", "结网", "作灶", "破屋", "坏垣", "余事勿取"
]

# 黄历"忌"项池（每日随机挑 2-3 条）
almanac_ji_pool: list[str] = [
    "嫁娶", "安葬", "行丧", "破土", "开市", "动土", "出行",
    "祈福", "入宅", "移徙", "安床", "修造", "上梁", "交易",
    "立券", "纳财", "栽种", "纳畜", "针灸", "伐木", "经络",
    "理发", "会亲友", "作灶", "冠笄", "裁衣", "结网", "词讼",
    "出火", "归宁"
]


def _make_rand(seed: int):
    """构造与前端一致的 LCG 伪随机函数"""
    s = seed

    def _rand() -> float:
        nonlocal s
        s = (s * 9301 + 49297) % 233280
        return s / 233280

    return _rand


def _shuffle_with_rand(items: list[str], rand) -> list[str]:
    """与 JS 的 sort(() => rand() - 0.5) 行为近似：基于 rand 重新排序

    注意：JS 的 sort 排序比较器返回 rand()-0.5 并不产生均匀洗牌，
    后端这里仅作"按种子稳定打乱顺序"用，分布不均亦可。
    实现采用给每个元素分配一个 rand() 作为 key 再排序，保证可复现。
    """
    keyed = [(rand(), x) for x in items]
    keyed.sort(key=lambda kv: kv[0])
    return [x for _, x in keyed]


def pick_almanac_yi(seed: int) -> list[str]:
    """按种子挑黄历宜项（3-4 条）

    与前端实现保持一致：rand 起始 s = seed + 53。
    """
    rand = _make_rand(seed + 53)
    count = 3 + int(rand() * 2)
    shuffled = _shuffle_with_rand(almanac_yi_pool, rand)
    return shuffled[:count]


def pick_almanac_ji(seed: int) -> list[str]:
    """按种子挑黄历忌项（2-3 条）

    与前端实现保持一致：rand 起始 s = seed + 89。
    """
    rand = _make_rand(seed + 89)
    count = 2 + int(rand() * 2)
    shuffled = _shuffle_with_rand(almanac_ji_pool, rand)
    return shuffled[:count]
