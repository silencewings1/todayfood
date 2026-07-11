"""日志收集器

按配置采集请求与模型交互详情，并在写入前完成脱敏和截断。
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.config import settings


_REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = {
    "password", "passwd", "token", "access_token", "refresh_token",
    "authorization", "api_key", "secret", "cookie", "session",
}
_KEY_VALUE_RE = re.compile(
    r'(?i)(\b(?:password|passwd|token|access_token|refresh_token|authorization|api_key|secret|cookie|session)\b'
    r'\s*[=:]\s*)("[^"\r\n]*"|[^&\s,;}]+)'
)
_BEARER_RE = re.compile(r"(?i)(\bBearer\s+)[A-Za-z0-9._~+/=-]+")


def _redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _REDACTED if str(key).lower() in _SENSITIVE_KEYS else _redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_value(item) for item in value]
    return value


def _redact_text(value: str) -> str:
    value = _KEY_VALUE_RE.sub(lambda match: match.group(1) + _REDACTED, value)
    return _BEARER_RE.sub(lambda match: match.group(1) + _REDACTED, value)


def _serialize(value: Any) -> str:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return _redact_text(value)
        return json.dumps(_redact_value(parsed), ensure_ascii=False, separators=(",", ":"))
    try:
        return json.dumps(_redact_value(value), ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return _redact_text(str(value))


def _truncate(value: str, max_chars: int) -> str:
    max_chars = max(0, max_chars)
    if len(value) <= max_chars:
        return value
    if max_chars <= 3:
        return value[:max_chars]
    return value[:max_chars - 3] + "..."


def _prepare(value: Any, max_chars: int) -> str | None:
    if value is None or value == "":
        return None
    return _truncate(_serialize(value), max_chars)


def log_api_call(*, method: str, path: str, status: int = 0,
                 cost_ms: float = 0, req_body: Any = None) -> None:
    """记录一次 API 调用。"""
    from admin.backend import db

    logs = settings.admin.logs
    body = _prepare(req_body, logs.api_body_max_chars) if logs.capture_api_body else None
    db.insert_api_log(
        method=method, path=path, status=status, cost_ms=cost_ms, req_body=body,
    )


def log_ai_call(*, agent: str, prompt: str = "", response: str = "", parsed=None,
                cost_ms: float = 0, success: bool = True, fallback: bool = False,
                error: str = "", tokens: int = 0) -> None:
    """记录一次 AI 调用及经过脱敏的交互详情。"""
    from admin.backend import db

    logs = settings.admin.logs
    if logs.capture_ai_content:
        saved_prompt = _prepare(prompt, logs.ai_prompt_max_chars)
        saved_response = _prepare(response, logs.ai_response_max_chars)
        saved_parsed = _prepare(parsed, logs.ai_response_max_chars)
    else:
        saved_prompt = saved_response = saved_parsed = None

    error_type = error.split(":", 1)[0][:100] if error else ""
    db.insert_ai_log(
        agent=agent, prompt=saved_prompt, response=saved_response, parsed=saved_parsed,
        cost_ms=cost_ms, success=success, fallback=fallback,
        error=error_type, tokens=tokens,
    )
