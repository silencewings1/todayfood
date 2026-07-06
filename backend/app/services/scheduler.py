"""每日食历定时任务

对应 TASKS.md 中的 A3：每日凌晨 00:00（北京时间）重新生成当日食历。

实现方式：
- 后台线程，每 6 小时检查一次日期
- 检测到日期变化时，预热新一天的缓存（提前生成，避免首个请求慢）
- 不依赖外部调度器（apscheduler 等），单进程足够

生产环境若多进程部署，可改为 Redis 分布式锁 + 定时任务，避免重复生成。
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings
from app.services.fortune_service import get_today_fortune

logger = logging.getLogger(__name__)


class DailyRefreshTask:
    """每日凌晨刷新食历缓存的轻量后台任务

    用法：
        task = DailyRefreshTask()
        task.start()  # 启动后台线程
        # task.stop()  # 关闭（可选）
    """

    def __init__(self, tz: str = "Asia/Shanghai", check_interval_sec: int = 6 * 3600) -> None:
        self.tz = tz
        self.check_interval = check_interval_sec
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._last_date: str | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="daily-refresh", daemon=True)
        self._thread.start()
        logger.info("DailyRefreshTask 已启动（检查间隔 %ss）", self.check_interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        # 启动时先记录当前日期，预热一次缓存
        try:
            now = datetime.now(ZoneInfo(self.tz))
            self._last_date = f"{now.year:04d}-{now.month:02d}-{now.day:02d}"
            logger.info("DailyRefreshTask 启动预热：当日 %s", self._last_date)
            get_today_fortune()  # 预热缓存
        except Exception as e:
            logger.warning("DailyRefreshTask 启动预热失败: %s", e)

        while not self._stop.is_set():
            # 等待下一次检查
            if self._stop.wait(self.check_interval):
                break

            try:
                now = datetime.now(ZoneInfo(self.tz))
                today_str = f"{now.year:04d}-{now.month:02d}-{now.day:02d}"
                if today_str != self._last_date:
                    logger.info("检测到日期切换 %s → %s，刷新缓存", self._last_date, today_str)
                    self._last_date = today_str
                    get_today_fortune()  # 触发新一天缓存生成
            except Exception as e:
                logger.warning("DailyRefreshTask 检查失败: %s", e)


# 全局单例
daily_refresh_task = DailyRefreshTask()
