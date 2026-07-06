"""签文池

从前端 src/data/signs.js 迁移而来。
pick_sign 函数从 sign_pool 中按种子稳定选一条。
"""
from __future__ import annotations

from typing import TypedDict


class Sign(TypedDict):
    name: str
    level: str
    text: str


sign_pool: list[Sign] = [
    {"name": "随遇而安签", "level": "上上签", "text": "胃需要被认真对待，热气会把犹豫蒸发。"},
    {"name": "热汤暖胃签", "level": "上上签", "text": "今日宜热汤主食，先暖胃，再想人生大事。"},
    {"name": "提神醒脑签", "level": "中吉", "text": "一点辣意可以唤醒精神，但今天别逞强。"},
    {"name": "清风轻食签", "level": "上签", "text": "今日宜清爽，让身体和心情都轻一点。"},
    {"name": "饭搭子签", "level": "上上签", "text": "和不知道吃什么的人一起吃饭，答案会自己出现。"},
    {"name": "温暖配置签", "level": "上签", "text": "一份主食 + 一份热汤 = 今日最低幸福配置。"},
    {"name": "奖励自己签", "level": "中吉", "text": "今日宜奖励自己，热量先欠着，心情先收下。"},
    {"name": "热闹聚餐签", "level": "上上签", "text": "今天适合和饭搭子一起吃，单人也可点双份快乐。"},
    {"name": "吃饭仪式签", "level": "上签", "text": "认真吃饭，是今天最小也最值得的仪式。"},
    {"name": "随便改就它签", "level": "中吉", "text": "今日食签：中吉。适合把\"随便\"改成\"就它\"。"},
    {"name": "清淡养胃签", "level": "上签", "text": "今天少点一次外卖试试，身体会悄悄松一口气。"},
    {"name": "小口慢咽签", "level": "上签", "text": "今日宜小口慢咽，连饭都认真了，别的事也是。"}
]


def pick_sign(seed: int) -> Sign:
    """按种子稳定抽一支签

    与前端 pickSign 算法一致：
        s = (seed * 9301 + 49297) % 233280
        r = s / 233280
        return sign_pool[floor(r * len)]
    """
    s = (seed * 9301 + 49297) % 233280
    r = s / 233280
    return sign_pool[int(r * len(sign_pool))]
