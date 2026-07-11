"""全局配置

配置来源与优先级（高 → 低）：
1. 环境变量（敏感信息如 OPENAI_API_KEY 必须走环境变量，不写入配置文件）
2. .env（本地开发常用，由 python-dotenv 自动加载到 os.environ）
3. config/app.toml + config/ai.toml（结构化配置，可提交到 git，便于版本管理）
4. 代码内默认值（保证零配置可用）

涉及文件：
- backend/config/app.toml  系统/服务/调度/admin 配置
- backend/config/ai.toml   AI 协议/模型/超时/各 agent 开关
- backend/.env             敏感信息 + 部署期覆盖（不入 git）
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 启动时自动加载 backend/.env（若存在），将其中变量注入 os.environ
# 这样 os.getenv 即可读到 .env 里的配置，无需手动 source
try:
    from dotenv import load_dotenv
    _BACKEND_ROOT = Path(__file__).resolve().parent.parent
    load_dotenv(_BACKEND_ROOT / ".env")
except ImportError:
    pass

# backend/config/ 目录
_CONFIG_DIR = _BACKEND_ROOT / "config"
_APP_CONFIG_PATH = _CONFIG_DIR / "app.toml"
_AI_CONFIG_PATH = _CONFIG_DIR / "ai.toml"


def _load_toml(path: Path) -> dict[str, Any]:
    """加载 toml 文件，不存在或解析失败时返回空 dict（保证服务能启动）"""
    if not path.exists():
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"[config] 加载 {path} 失败: {e}，使用默认值")
        return {}


# 原始 toml 配置（保留以便其他模块读取未在 Settings 中暴露的字段）
app_toml: dict[str, Any] = _load_toml(_APP_CONFIG_PATH)
ai_toml: dict[str, Any] = _load_toml(_AI_CONFIG_PATH)


def _deep_get(d: dict, *keys, default=None):
    """从嵌套 dict 中安全取值"""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _split_origins(value: str) -> list[str]:
    """把逗号分隔的字符串切成 origin 列表"""
    return [s.strip() for s in value.split(",") if s.strip()]


# =========================================================================
# AI 配置
# =========================================================================

@dataclass(frozen=True)
class AgentConfig:
    """单个 AI 接入点配置"""
    enabled: bool
    model: str
    temperature: float


@dataclass(frozen=True)
class AISettings:
    """AI 整体配置"""
    enabled: bool
    api_protocol: str            # "chat_completions" | "responses"
    api_key: str                 # 仅从环境变量读取
    base_url: str
    model: str
    timeout: int                 # HTTP 客户端超时
    ai_timeout: int              # AI 调用整体超时（超时回退本地）
    max_retries: int
    agents: dict[str, AgentConfig] = field(default_factory=dict)

    def agent(self, name: str) -> AgentConfig:
        """获取某个 agent 的配置，缺失时返回禁用默认值"""
        return self.agents.get(name, AgentConfig(enabled=False, model="", temperature=0.5))


def _build_ai_settings() -> AISettings:
    """从 ai.toml + 环境变量合成 AISettings

    环境变量覆盖 toml 同名字段：
      USE_AI         -> ai.enabled
      OPENAI_API_KEY -> ai.api_key（仅环境变量，不入文件）
      OPENAI_BASE_URL-> ai.base_url
      OPENAI_MODEL   -> ai.model
      AI_PROTOCOL    -> ai.api_protocol
      AI_TIMEOUT     -> ai.timeout
      AI_CALL_TIMEOUT-> ai.ai_timeout
      AI_MAX_RETRIES -> ai.max_retries
    """
    ai_sec = ai_toml.get("ai", {})

    enabled = os.getenv("USE_AI", str(ai_sec.get("enabled", False))).lower() in ("1", "true", "yes")
    api_key = os.getenv("OPENAI_API_KEY", "")  # 仅环境变量
    base_url = os.getenv("OPENAI_BASE_URL", ai_sec.get("base_url", ""))
    model = os.getenv("OPENAI_MODEL", ai_sec.get("model", "gpt-4o-mini"))
    api_protocol = os.getenv("AI_PROTOCOL", ai_sec.get("api_protocol", "chat_completions"))
    timeout = int(os.getenv("AI_TIMEOUT", ai_sec.get("timeout", 30)))
    ai_timeout = int(os.getenv("AI_CALL_TIMEOUT", ai_sec.get("ai_timeout", 20)))
    max_retries = int(os.getenv("AI_MAX_RETRIES", ai_sec.get("max_retries", 2)))

    agents: dict[str, AgentConfig] = {}
    for name, cfg in (ai_sec.get("agents") or {}).items():
        if not isinstance(cfg, dict):
            continue
        agents[name] = AgentConfig(
            enabled=bool(cfg.get("enabled", False)),
            model=str(cfg.get("model", "") or ""),
            temperature=float(cfg.get("temperature", 0.5)),
        )

    return AISettings(
        enabled=enabled,
        api_protocol=api_protocol,
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout=timeout,
        ai_timeout=ai_timeout,
        max_retries=max_retries,
        agents=agents,
    )


# =========================================================================
# 系统 / 应用配置
# =========================================================================

@dataclass(frozen=True)
class SchedulerConfig:
    """每日食历刷新调度"""
    check_interval_sec: int = 21600  # 6 小时


@dataclass(frozen=True)
class AdminLogsConfig:
    """后台日志采集、查询与保留参数"""
    query_days: int = 30
    query_max_rows: int = 10000
    capture_api_body: bool = True
    capture_ai_content: bool = True
    api_body_max_chars: int = 4096
    ai_prompt_max_chars: int = 12000
    ai_response_max_chars: int = 12000
    retention_days: int = 30
    retention_max_rows: int = 10000


@dataclass(frozen=True)
class AdminConfig:
    """后台管理配置"""
    host: str = "0.0.0.0"
    port: int = 9082
    monitored_health_url: str = "http://127.0.0.1:8000/health"
    session_cookie: str = "admin_token"
    session_max_age: int = 86400
    username: str = ""
    password: str = ""
    logs: AdminLogsConfig = field(default_factory=AdminLogsConfig)


def _build_admin_config() -> AdminConfig:
    """从 app.toml + 环境变量合成 AdminConfig"""
    sec = app_toml.get("admin", {})
    logs_sec = sec.get("logs", {}) if isinstance(sec, dict) else {}

    return AdminConfig(
        host=os.getenv("ADMIN_HOST", sec.get("host", "0.0.0.0")),
        port=int(os.getenv("ADMIN_PORT", sec.get("port", 9082))),
        monitored_health_url=os.getenv(
            "MONITORED_HEALTH_URL",
            sec.get("monitored_health_url", "http://127.0.0.1:8000/health"),
        ),
        session_cookie=os.getenv("ADMIN_SESSION_COOKIE", sec.get("session_cookie", "admin_token")),
        session_max_age=int(os.getenv("ADMIN_SESSION_MAX_AGE", sec.get("session_max_age", 86400))),
        username=os.getenv("ADMIN_USERNAME", sec.get("username", "")),
        password=os.getenv("ADMIN_PASSWORD", sec.get("password", "")),
        logs=AdminLogsConfig(
            query_days=int(os.getenv("ADMIN_LOG_QUERY_DAYS", logs_sec.get("query_days", 30))),
            query_max_rows=int(os.getenv("ADMIN_LOG_MAX_ROWS", logs_sec.get("query_max_rows", 10000))),
            capture_api_body=os.getenv(
                "ADMIN_LOG_CAPTURE_API_BODY", str(logs_sec.get("capture_api_body", True))
            ).lower() in ("1", "true", "yes"),
            capture_ai_content=os.getenv(
                "ADMIN_LOG_CAPTURE_AI_CONTENT", str(logs_sec.get("capture_ai_content", True))
            ).lower() in ("1", "true", "yes"),
            api_body_max_chars=int(os.getenv(
                "ADMIN_LOG_API_BODY_MAX_CHARS", logs_sec.get("api_body_max_chars", 4096)
            )),
            ai_prompt_max_chars=int(os.getenv(
                "ADMIN_LOG_AI_PROMPT_MAX_CHARS", logs_sec.get("ai_prompt_max_chars", 12000)
            )),
            ai_response_max_chars=int(os.getenv(
                "ADMIN_LOG_AI_RESPONSE_MAX_CHARS", logs_sec.get("ai_response_max_chars", 12000)
            )),
            retention_days=int(os.getenv(
                "ADMIN_LOG_RETENTION_DAYS", logs_sec.get("retention_days", 30)
            )),
            retention_max_rows=int(os.getenv(
                "ADMIN_LOG_RETENTION_MAX_ROWS", logs_sec.get("retention_max_rows", 10000)
            )),
        ),
    )


def _build_scheduler_config() -> SchedulerConfig:
    """从 app.toml + 环境变量合成 SchedulerConfig"""
    sec = app_toml.get("scheduler", {})
    return SchedulerConfig(
        check_interval_sec=int(os.getenv("SCHEDULER_CHECK_INTERVAL",
                                        sec.get("check_interval_sec", 21600))),
    )


@dataclass(frozen=True)
class Settings:
    # ===== 服务 =====
    host: str = os.getenv("HOST", app_toml.get("server", {}).get("host", "127.0.0.1"))
    port: int = int(os.getenv("PORT", app_toml.get("server", {}).get("port", 8000)))
    # 允许跨域的前端地址列表
    frontend_origins: tuple[str, ...] = tuple(
        _split_origins(os.getenv("FRONTEND_ORIGIN", ""))
        or app_toml.get("server", {}).get("frontend_origins")
        or ["http://localhost:5173"]
    )

    # ===== 应用 =====
    timezone: str = os.getenv("TZ", app_toml.get("app", {}).get("timezone", "Asia/Shanghai"))
    cache_enabled: bool = os.getenv(
        "CACHE_ENABLED",
        str(app_toml.get("app", {}).get("cache_enabled", True))
    ).lower() in ("1", "true", "yes")
    database_path: str = os.getenv(
        "TODAYFOOD_DB_PATH",
        str(Path(__file__).resolve().parents[1] / "data" / "log.db"),
    )

    # ===== AI 选菜频率限制 =====
    rate_limit_window_sec: int = int(os.getenv(
        "RATE_LIMIT_WINDOW_SEC",
        app_toml.get("app", {}).get("rate_limit_window_sec", 60)
    ))
    rate_limit_max_calls: int = int(os.getenv(
        "RATE_LIMIT_MAX_CALLS",
        app_toml.get("app", {}).get("rate_limit_max_calls", 5)
    ))

    # ===== 调度 =====
    scheduler: SchedulerConfig = field(default_factory=_build_scheduler_config)

    # ===== admin =====
    admin: AdminConfig = field(default_factory=_build_admin_config)

    # ===== AI（从 ai.toml + 环境变量合成） =====
    # 保持向后兼容：旧代码读 settings.use_ai 仍可用
    use_ai: bool = _build_ai_settings().enabled

    @property
    def ai(self) -> AISettings:
        """AI 完整配置（每次读取重新合成，便于热加载）"""
        return _build_ai_settings()

    # ===== 向后兼容的快捷属性 =====
    @property
    def frontend_origin(self) -> str:
        """旧代码兼容：返回第一个 origin"""
        return self.frontend_origins[0] if self.frontend_origins else ""

    @property
    def openai_api_key(self) -> str:
        return _build_ai_settings().api_key

    @property
    def openai_base_url(self) -> str:
        return _build_ai_settings().base_url

    @property
    def openai_model(self) -> str:
        return _build_ai_settings().model


settings = Settings()
