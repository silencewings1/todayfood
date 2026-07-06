"""每日食历缓存

最简内存缓存：按日期 key 缓存今日食历结果，凌晨 0 点切换日期自动失效。
生产可替换为 Redis，接口保持一致（get/set/clear）。
"""
from __future__ import annotations

import threading
from typing import Any, Optional


class DailyCache:
    """按日期键的内存缓存

    线程安全（加锁）。key 通常是 today_info()['date']。
    """

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            return self._store.get(key)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            # 清理非当日旧 key（仅保留当前）
            self._store = {key: value}

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# 全局单例
daily_cache = DailyCache()
