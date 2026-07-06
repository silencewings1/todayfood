"""种子与抽签算法稳定性测试

验证后端实现与前端算法在「同种子同结果」这一不变量上成立。
"""
from __future__ import annotations

from app.core.picker import (
    pick_any,
    pick_avoid,
    pick_by_tags,
    pick_lucky,
    pick_sign_obj,
    pick_suitable,
    pick_today_food,
)
from app.core.seed import pick_sign_no, seeded_random, today_info
from app.data.foods import food_pool
from app.data.signs import sign_pool


def test_today_info_seed_format():
    """today.seed 应为 YYYYMMDD 格式"""
    info = today_info()
    assert info["seed"] > 20240000, info
    assert 1 <= int(str(info["seed"])[6:8]) <= 31


def test_seeded_random_deterministic():
    """相同种子应产生相同序列"""
    r1 = seeded_random(20260706)
    r2 = seeded_random(20260706)
    seq1 = [r1() for _ in range(10)]
    seq2 = [r2() for _ in range(10)]
    assert seq1 == seq2


def test_pick_today_food_stable():
    """同一种子应稳定返回同一道菜"""
    f1 = pick_today_food(20260706)
    f2 = pick_today_food(20260706)
    assert f1["id"] == f2["id"]
    assert f1 in food_pool


def test_pick_today_food_different_seed():
    """不同种子应可能返回不同菜品（不强制一定不同，但跨多日应有变化）"""
    ids = {pick_today_food(20260701 + i)["id"] for i in range(0, 30)}
    assert len(ids) > 1, "30 天种子下应至少出现 2 道不同菜"


def test_pick_sign_no_in_range():
    """签号应在 1-99 之间"""
    for seed in (20260706, 20260101, 20261231):
        no = pick_sign_no(seed)
        assert 1 <= no <= 99


def test_pick_sign_obj_stable():
    """同种子应稳定返回同一支签"""
    s1 = pick_sign_obj(20260706)
    s2 = pick_sign_obj(20260706)
    assert s1 == s2
    assert s1 in sign_pool


def test_pick_suitable_is_group_of_3():
    """宜吃组应为 3 条"""
    grp = pick_suitable(20260706)
    assert len(grp) == 3
    assert all(isinstance(x, str) for x in grp)


def test_pick_avoid_count_in_range():
    """忌吃清单应为 3-5 条"""
    av = pick_avoid(20260706)
    assert 3 <= len(av) <= 5
    assert len(set(av)) == len(av), "忌吃项不应重复"


def test_pick_lucky_has_three_fields():
    """幸运三件套应含 flavor/color/direction"""
    lucky = pick_lucky(20260706)
    assert set(lucky.keys()) == {"flavor", "color", "direction"}
    assert all(isinstance(v, str) and v for v in lucky.values())


def test_pick_by_tags_prefers_matching():
    """偏好命中时应倾向于返回匹配菜品"""
    # hungry + spicy 都命中的菜品是 spicy-pot / sour-noodle
    matched_ids = set()
    for _ in range(20):
        f = pick_by_tags({"mood": "spicy", "flavor": "spicy"}, salt_seed=42)
        matched_ids.add(f["id"])
    # 多次抽样下应至少出现一个 spicy 命中菜
    spicy_foods = [f for f in food_pool if "spicy" in f["tags"]["flavor"] and "spicy" in f["tags"]["mood"]]
    assert any(f["id"] in matched_ids for f in spicy_foods)


def test_pick_any_excludes_id():
    """pick_any 应正确排除指定 id"""
    for _ in range(10):
        f = pick_any(exclude_id="tomato-beef")
        assert f["id"] != "tomato-beef"
