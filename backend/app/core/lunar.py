"""农历转换与干支计算

纯 Python 实现，不依赖第三方库。
内置 1900-2099 农历数据表（编码方式同 lunardate），支持公历转农历、天干地支纪年纪月、农历日中文格式化。
"""
from __future__ import annotations

from datetime import date

# 天干地支
_STEMS = "甲乙丙丁戊己庚辛壬癸"
_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

# 农历日中文
_DAY_PREFIX = ["初", "十", "廿", "卅"]
_DAY_DIGIT = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]

# 农历数据表 1900-2099
# 编码（同 lunardate）:
#   bit 0-3:   闰月月份 (0=无)
#   bit 4-15:  腊月至正月大小月 (1=30天, 0=29天)，bit 15=正月, bit 4=腊月
#   bit 16:    闰月大小月 (1=30天, 0=29天)
_YEAR_INFOS = [
    0x04bd8,                                    # 1900
    0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950,  # 1905
    0x16554, 0x056a0, 0x09ad0, 0x055d2, 0x04ae0,  # 1910
    0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540,  # 1915
    0x0d6a0, 0x0ada2, 0x095b0, 0x14977, 0x04970,  # 1920
    0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54,  # 1925
    0x02b60, 0x09570, 0x052f2, 0x04970, 0x06566,  # 1930
    0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60,  # 1935
    0x186e3, 0x092e0, 0x1c8d7, 0x0c950, 0x0d4a0,  # 1940
    0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0,  # 1945
    0x092d0, 0x0d2b2, 0x0a950, 0x0b557, 0x06ca0,  # 1950
    0x0b550, 0x15355, 0x04da0, 0x0a5d0, 0x14573,  # 1955
    0x052b0, 0x0a9a8, 0x0e950, 0x06aa0, 0x0aea6,  # 1960
    0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260,  # 1965
    0x0f263, 0x0d950, 0x05b57, 0x056a0, 0x096d0,  # 1970
    0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250,  # 1975
    0x0d558, 0x0b540, 0x0b5a0, 0x195a6, 0x095b0,  # 1980
    0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50,  # 1985
    0x06d40, 0x0af46, 0x0ab60, 0x09570, 0x04af5,  # 1990
    0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58,  # 1995
    0x05ac0, 0x0ab60, 0x096d5, 0x092e0, 0x0c960,  # 2000
    0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0,  # 2005
    0x0abb7, 0x025d0, 0x092d0, 0x0cab5, 0x0a950,  # 2010
    0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0,  # 2015
    0x0a5b0, 0x15176, 0x052b0, 0x0a930, 0x07954,  # 2020
    0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6,  # 2025
    0x0a4e0, 0x0d260, 0x0ea65, 0x0d530, 0x05aa0,  # 2030
    0x076a3, 0x096d0, 0x04afb, 0x04ad0, 0x0a4d0,  # 2035
    0x1d0b6, 0x0d250, 0x0d520, 0x0dd45, 0x0b5a0,  # 2040
    0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0,  # 2045
    0x0aa50, 0x1b255, 0x06d20, 0x0ada0, 0x14b63,  # 2050
    0x09370, 0x049f8, 0x04970, 0x064b0, 0x168a6,  # 2055
    0x0ea50, 0x06aa0, 0x1a6c4, 0x0aae0, 0x092e0,  # 2060
    0x0d2e3, 0x0c960, 0x0d557, 0x0d4a0, 0x0da50,  # 2065
    0x05d55, 0x056a0, 0x0a6d0, 0x055d4, 0x052d0,  # 2070
    0x0a9b8, 0x0a950, 0x0b4a0, 0x0b6a6, 0x0ad50,  # 2075
    0x055a0, 0x0aba4, 0x0a5b0, 0x052b0, 0x0b273,  # 2080
    0x06930, 0x07337, 0x06aa0, 0x0ad50, 0x14b55,  # 2085
    0x04b60, 0x0a570, 0x054e4, 0x0d160, 0x0e968,  # 2090
    0x0d520, 0x0daa0, 0x16aa6, 0x056d0, 0x04ae0,  # 2095
    0x0a9d4, 0x0a2d0, 0x0d150, 0x0f252,            # 2099
]


def _year_days(year_info: int) -> int:
    """农历年总天数"""
    res = 29 * 12
    leap = year_info % 16
    if leap:
        res += 29
    info = year_info // 16
    for _ in range(12 + (1 if leap else 0)):
        if info % 2 == 1:
            res += 1
        info //= 2
    return res


_YEAR_DAYS = [_year_days(yi) for yi in _YEAR_INFOS]


def _month_days(year_info: int, month: int, is_leap: bool = False) -> int:
    """农历某月天数"""
    if is_leap:
        return (year_info >> 16) % 2 + 29
    return (year_info >> (16 - month)) % 2 + 29


def solar_to_lunar(d: date) -> tuple[int, int, int, bool]:
    """公历 date 转农历

    返回 (lunar_year, lunar_month, lunar_day, is_leap_month)
    以农历正月初一为年界。
    """
    base = date(1900, 1, 31)  # 农历 1900-01-01
    offset = (d - base).days

    ly = 1900
    for idx, yd in enumerate(_YEAR_DAYS):
        if offset < yd:
            ly = 1900 + idx
            break
        offset -= yd

    year_info = _YEAR_INFOS[ly - 1900]
    leap = year_info % 16

    lm = 1
    while lm <= 12:
        md = _month_days(year_info, lm)
        if offset < md:
            return ly, lm, offset + 1, False
        offset -= md
        # 闰月紧跟在正常月之后
        if leap == lm:
            lmd = _month_days(year_info, lm, is_leap=True)
            if offset < lmd:
                return ly, lm, offset + 1, True
            offset -= lmd
        lm += 1

    return ly, lm, offset + 1, False


def _gan_zhi_year(lunar_year: int) -> str:
    """天干地支纪年（以农历正月初一为界）"""
    s = (lunar_year - 4) % 10
    b = (lunar_year - 4) % 12
    return _STEMS[s] + _BRANCHES[b]


def _gan_zhi_month(lunar_year: int, lunar_month: int) -> str:
    """天干地支纪月（五虎遁年起月诀）

    月支固定：正月寅、二月卯、…、十二月丑
    月干由年干推算：甲己起丙、乙庚起戊、丙辛起庚、丁壬起壬、戊癸起甲
    """
    year_stem = (lunar_year - 4) % 10
    # 正月天干起始索引
    stem_start = [2, 4, 6, 8, 0][year_stem % 5]
    month_stem = (stem_start + lunar_month - 1) % 10
    # 正月=寅(索引2)，依次递增
    month_branch = (2 + lunar_month - 1) % 12
    return _STEMS[month_stem] + _BRANCHES[month_branch]


def _format_day(day: int) -> str:
    """农历日中文（初一 ~ 三十）"""
    if day == 10:
        return "初十"
    if day == 20:
        return "二十"
    if day == 30:
        return "三十"
    return _DAY_PREFIX[day // 10] + _DAY_DIGIT[day % 10]


def lunar_date_text(d: date) -> str:
    """公历转农历干支日期文本，如「丙午年 甲午月 廿三」"""
    ly, lm, ld, _ = solar_to_lunar(d)
    year_gz = _gan_zhi_year(ly)
    month_gz = _gan_zhi_month(ly, lm)
    day_str = _format_day(ld)
    return f"{year_gz}年 {month_gz}月 {day_str}"
