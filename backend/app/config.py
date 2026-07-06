"""全局配置

加载优先级（高 → 低）：
1. 环境变量（敏感信息如 OPENAI_API_KEY 必须走环境变量，不写入配置文件）
2. config/ai.toml（结构化配置，可提交到 git，便于版本管理）
3. 代码内默认值（保证零配置可用）
"""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# backend/ 目录
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_AI_CONFIG_PATH = _BACKEND_ROOT / "config" / "ai.toml"


def _load_ai_toml() -> dict[str, Any]:
    """加载 config/ai.toml

    文件不存在或解析失败时返回空 dict，回退默认值。
    """
    if not _AI_CONFIG_PATH.exists():
        return {}
    try:
        with open(_AI_CONFIG_PATH, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        # 不抛异常，保证服务能启动
        print(f"[config] 加载 {_AI_CONFIG_PATH} 失败: {e}，使用默认值")
        return {}


# 原始 toml 配置（保留以便其他模块读取未在 Settings 中暴露的字段）
ai_toml: dict[str, Any] = _load_ai_toml()


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
    """从 toml + 环境变量合成 AISettings

    环境变量覆盖 toml 同名字段：
      USE_AI         -> ai.enabled
      OPENAI_API_KEY -> ai.api_key（仅环境变量，不入文件）
      OPENAI_BASE_URL-> ai.base_url
      OPENAI_MODEL   -> ai.model
      AI_PROTOCOL    -> ai.api_protocol
    """
    ai_sec = ai_toml.get("ai", {})

    # 环境变量覆盖（优先级最高）
    enabled = os.getenv("USE_AI", str(ai_sec.get("enabled", False))).lower() in ("1", "true", "yes")
    api_key = os.getenv("OPENAI_API_KEY", "")  # 仅环境变量
    base_url = os.getenv("OPENAI_BASE_URL", ai_sec.get("base_url", ""))
    model = os.getenv("OPENAI_MODEL", ai_sec.get("model", "gpt-4o-mini"))
    api_protocol = os.getenv("AI_PROTOCOL", ai_sec.get("api_protocol", "chat_completions"))
    timeout = int(os.getenv("AI_TIMEOUT", ai_sec.get("timeout", 30)))
    ai_timeout = int(os.getenv("AI_CALL_TIMEOUT", ai_sec.get("ai_timeout", 20)))
    max_retries = int(os.getenv("AI_MAX_RETRIES", ai_sec.get("max_retries", 2)))

    # 各 agent 配置
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


@dataclass(frozen=True)
class Settings:
    # ===== 服务 =====
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # ===== 时区 =====
    timezone: str = os.getenv("TZ", "Asia/Shanghai")

    # ===== 缓存 =====
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "1") == "1"

    # ===== AI（从 toml + 环境变量合成） =====
    # 保持向后兼容：旧代码读 settings.use_ai / settings.openai_* 仍可用
    use_ai: bool = _build_ai_settings().enabled

    @property
    def ai(self) -> AISettings:
        """AI 完整配置（每次读取重新合成，便于热加载）"""
        return _build_ai_settings()

    # ===== 向后兼容的快捷属性 =====
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
