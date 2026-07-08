"""频率限制器

滑动窗口计数：在 window_sec 秒内最多允许 max_calls 次调用。
超过后返回 True（被限制），窗口过期后自动解禁。

参数从 config/app.toml [app] section 读取，支持环境变量覆盖。
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    """频率限制配置"""
    window_sec: int = 60       # 时间窗口（秒）
    max_calls: int = 5         # 窗口内最大调用次数


class RateLimiter:
    """滑动窗口频率限制器

    线程安全。每次调用 check() 记录当前时间戳，
    如果窗口内调用次数超过 max_calls，返回 True（被限制）。
    """

    def __init__(self, window_sec: int = 60, max_calls: int = 5) -> None:
        self._window_sec = window_sec
        self._max_calls = max_calls
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def check(self) -> bool:
        """检查是否被频率限制

        Returns:
            True = 已超限（应该走数据库兜底），False = 未超限（可以调 AI）
        """
        now = time.time()
        cutoff = now - self._window_sec
        with self._lock:
            # 清理过期时间戳
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()
            if len(self._timestamps) >= self._max_calls:
                return True
            self._timestamps.append(now)
            return False

    def remaining(self) -> int:
        """当前窗口内剩余可用次数"""
        now = time.time()
        cutoff = now - self._window_sec
        with self._lock:
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()
            return max(0, self._max_calls - len(self._timestamps))

    def update_config(self, window_sec: int, max_calls: int) -> None:
        """热更新配置"""
        with self._lock:
            self._window_sec = window_sec
            self._max_calls = max_calls


# 全局单例（配置在 fortune_service 中初始化时注入）
rate_limiter = RateLimiter()
