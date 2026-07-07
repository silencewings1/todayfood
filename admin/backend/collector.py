"""日志收集器

提供简洁的写入接口，供中间件和 AI Provider 调用。
延迟导入 db 模块，避免循环依赖。
"""
from __future__ import annotations

import json
from typing import Any


def log_api_call(*, method: str, path: str, client: str = "", status: int = 0,
                 cost_ms: float = 0, req_body: str = "", resp_body: Any = None,
                 ua: str = "") -> None:
    """记录一次 API 调用"""
    from admin.backend import db

    # 响应体截断摘要
    resp_summary = ""
    if resp_body is not None:
        try:
            text = resp_body if isinstance(resp_body, str) else json.dumps(resp_body, ensure_ascii=False)
            resp_summary = text[:300]
        except Exception:
            resp_summary = str(resp_body)[:300]

    db.insert_api_log(
        method=method, path=path, client=client, status=status,
        cost_ms=cost_ms, req_body=req_body[:500], resp_summary=resp_summary, ua=ua,
    )


def log_ai_call(*, agent: str, prompt: str = "", response: str = "", parsed: Any = None,
                cost_ms: float = 0, success: bool = True, fallback: bool = False,
                error: str = "", tokens: int = 0) -> None:
    """记录一次 AI 模型调用"""
    from admin.backend import db

    parsed_str = ""
    if parsed is not None:
        try:
            parsed_str = json.dumps(parsed, ensure_ascii=False)[:500]
        except Exception:
            parsed_str = str(parsed)[:500]

    db.insert_ai_log(
        agent=agent, prompt=prompt[:1000], response=response[:500],
        parsed=parsed_str, cost_ms=cost_ms, success=success,
        fallback=fallback, error=error[:500], tokens=tokens,
    )
