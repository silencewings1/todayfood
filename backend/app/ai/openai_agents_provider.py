"""基于 openai-agents SDK 的 Provider 实现

使用 OpenAI Agents SDK 实现 AIProvider 接口，支持两种 API 协议：
- chat_completions: POST /v1/chat/completions（兼容 OpenAI 官方 + 绝大多数第三方服务）
- responses:        POST /v1/responses（OpenAI 官方新协议）

协议通过 config/ai.toml 的 ai.api_protocol 字段切换，也支持环境变量 AI_PROTOCOL 覆盖。

三个 AI 接入点（对应 TASKS.md）：
- AI1 parse_note:      note_parser agent，自由文本解析为结构化偏好 JSON
- AI2 personalize_reason: reason_writer agent，生成个性化推荐理由
- AI3 generate_sign:   sign_generator agent，动态生成签文

每个 agent 可在 ai.toml 中独立开关、配置模型与温度。
所有方法均带异常兜底，失败返回 None / 空结果，不影响主流程。
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from app.ai.base import AIProvider, NoteParseResult
from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIAgentsProvider(AIProvider):
    """基于 openai-agents SDK 的 AI 实现

    协议选择：
        api_protocol = "chat_completions"  -> OpenAIChatCompletionsModel
        api_protocol = "responses"         -> OpenAIResponsesModel

    第三方兼容服务（deepseek/moonshot/通义千问等）通常只支持 chat_completions。
    """

    def __init__(self) -> None:
        ai = settings.ai

        if not ai.api_key:
            raise RuntimeError(
                "AI 已启用但 OPENAI_API_KEY 未设置，请配置环境变量或在 .env 中填入"
            )

        # 延迟导入：仅在 AI 启用时才加载 SDK
        try:
            from agents import Agent, OpenAIChatCompletionsModel, OpenAIResponsesModel
            from openai import AsyncOpenAI
        except ImportError as e:
            raise RuntimeError(
                "未安装 openai-agents SDK，请执行: pip install openai-agents"
            ) from e

        # 构造异步 OpenAI 客户端（兼容 base_url 代理）
        client_kwargs: dict = {"api_key": ai.api_key, "timeout": ai.timeout}
        if ai.base_url:
            client_kwargs["base_url"] = ai.base_url
        self._client = AsyncOpenAI(**client_kwargs)

        # 根据协议选择 Model 包装器
        self._api_protocol = ai.api_protocol
        if self._api_protocol == "responses":
            model_cls = OpenAIResponsesModel
            protocol_desc = "Responses API (/v1/responses)"
        else:
            # 默认与第三方兼容都用 chat_completions
            model_cls = OpenAIChatCompletionsModel
            protocol_desc = "Chat Completions API (/v1/chat/completions)"
            if self._api_protocol != "chat_completions":
                logger.warning(
                    "未知 api_protocol=%s，回退 chat_completions", self._api_protocol
                )
                self._api_protocol = "chat_completions"

        logger.info(
            "AI Provider 使用 %s | base_url=%s | model=%s",
            protocol_desc, ai.base_url or "(OpenAI 官方)", ai.model,
        )

        # 构造默认 model 实例（全局模型）
        self._default_model = model_cls(model=ai.model, openai_client=self._client)

        # 构造三个独立 Agent
        # 每个 Agent 的 model 可单独覆盖，temperature 单独配置
        self._note_agent = self._build_agent(
            name="note-parser",
            agent_key="note_parser",
            instructions=(
                "你是一个美食偏好解析助手。用户会输入一段自由文本描述想吃的食物，"
                "你需要解析为结构化偏好。返回严格的 JSON：\n"
                '{"mood": "tired|hungry|sad|happy|busy|spicy|no-appetite|treat|null", '
                '"flavor": "light|spicy|sour-sweet|sour-spicy|savory|heavy|milky|fresh|null", '
                '"keywords": ["..."]}\n'
                "mood/flavor 找不到就给 null。keywords 是从文本中提取的食物关键词。"
                "只返回 JSON，不要任何额外说明。"
            ),
            model_cls=model_cls,
        )

        self._reason_agent = self._build_agent(
            name="reason-writer",
            agent_key="reason_writer",
            instructions=(
                "你是「今日宜吃」小程序的文案。根据用户心情和偏好，"
                "为指定菜品写一句 30-50 字的个性化推荐理由，语气活泼可爱。"
                "只输出理由文案本身，不要标题、不要引号。"
            ),
            model_cls=model_cls,
        )

        self._sign_agent = self._build_agent(
            name="sign-generator",
            agent_key="sign_generator",
            instructions=(
                "你是「今日宜吃」的签文生成器。生成一条当日限定签文，"
                "包含 name（4-6 字短签名，含\"签\"字）、level（上上签/上签/中吉/中签）、"
                "text（20-40 字签文内容，活泼可爱风）。返回严格 JSON："
                '{"name":"...","level":"...","text":"..."}'
                "只返回 JSON。"
            ),
            model_cls=model_cls,
        )

    def _build_agent(self, *, name: str, agent_key: str, instructions: str, model_cls):
        """构造单个 Agent

        - 读取 ai.toml 中 [ai.agents.<agent_key>] 的配置
        - enabled=false 时仍构造（但上层调用前会检查 enabled）
        - model 为空时用全局默认 model
        - temperature 通过 model_settings 传入
        """
        from agents import Agent, ModelSettings

        cfg = settings.ai.agent(agent_key)
        # agent 级别 model 覆盖全局
        model_instance = model_cls(
            model=cfg.model or settings.ai.model,
            openai_client=self._client,
        )

        return Agent(
            name=name,
            instructions=instructions,
            model=model_instance,
            model_settings=ModelSettings(temperature=cfg.temperature),
        )

    @property
    def name(self) -> str:
        return f"openai-agents({self._api_protocol})"

    @property
    def enabled(self) -> bool:
        return True

    async def _run_with_timeout(self, agent, prompt: str):
        """带超时地执行 Agent

        超过 ai.ai_timeout 秒未返回，抛出 TimeoutError，由调用方 catch 后回退本地。
        """
        from agents import Runner
        return await asyncio.wait_for(
            Runner.run(agent, prompt),
            timeout=settings.ai.ai_timeout,
        )

    @staticmethod
    def _log_ai(agent: str, prompt: str, response: str, parsed, *,
                cost_ms: float, success: bool, fallback: bool, error: str = "") -> None:
        """写入 AI 调用日志（admin 后台用）"""
        try:
            from admin.backend.collector import log_ai_call
            log_ai_call(
                agent=agent, prompt=prompt, response=response, parsed=parsed,
                cost_ms=cost_ms, success=success, fallback=fallback, error=error,
            )
        except Exception:
            pass  # 日志失败不影响主流程

    async def parse_note(self, note: str, *, today_seed: int = 0) -> NoteParseResult:
        """AI1: 解析「想吃点啥」自由文本"""
        cfg = settings.ai.agent("note_parser")
        if not cfg.enabled or not note or not note.strip():
            return NoteParseResult(prefs=None, note_raw=note)

        import time
        start = time.perf_counter()
        prompt_text = note.strip()
        try:
            result = await self._run_with_timeout(self._note_agent, prompt_text)
            text = self._extract_text(result)
            prefs = self._safe_parse_json(text)
            cost_ms = (time.perf_counter() - start) * 1000
            if prefs is None:
                self._log_ai("note_parser", prompt_text, text, None,
                             cost_ms=cost_ms, success=False, fallback=True, error="JSON解析失败")
                return NoteParseResult(prefs=None, note_raw=note)
            # 兼容字段：null / 缺失都统一成 None
            mood = prefs.get("mood")
            flavor = prefs.get("flavor")
            if mood in ("", "null"):
                mood = None
            if flavor in ("", "null"):
                flavor = None
            result_obj = {"mood": mood, "flavor": flavor, "keywords": prefs.get("keywords", [])}
            self._log_ai("note_parser", prompt_text, text, result_obj,
                         cost_ms=cost_ms, success=True, fallback=False)
            return NoteParseResult(
                prefs={"mood": mood, "flavor": flavor, "note": note, "keywords": prefs.get("keywords", [])},
                note_raw=note, extra={"raw": text},
            )
        except asyncio.TimeoutError:
            cost_ms = (time.perf_counter() - start) * 1000
            self._log_ai("note_parser", prompt_text, "", None,
                         cost_ms=cost_ms, success=False, fallback=True, error=f"超时{settings.ai.ai_timeout}s")
            logger.warning("AI parse_note 超时(%ss)，回退本地兜底", settings.ai.ai_timeout)
            return NoteParseResult(prefs=None, note_raw=note)
        except Exception as e:
            cost_ms = (time.perf_counter() - start) * 1000
            self._log_ai("note_parser", prompt_text, "", None,
                         cost_ms=cost_ms, success=False, fallback=True, error=str(e))
            logger.warning("AI parse_note 失败，回退本地兜底: %s", e)
            return NoteParseResult(prefs=None, note_raw=note)

    async def personalize_reason(self, food: dict, prefs: dict, *, today_seed: int = 0) -> Optional[str]:
        """AI2: 生成个性化推荐理由"""
        cfg = settings.ai.agent("reason_writer")
        if not cfg.enabled:
            return None

        import time
        start = time.perf_counter()
        prompt = (
            f"菜品：{food.get('title')}（{food.get('category')}）\n"
            f"默认理由：{food.get('reason')}\n"
            f"用户心情：{prefs.get('mood') or '未知'}\n"
            f"口味偏好：{prefs.get('flavor') or '未知'}\n"
            f"想吃点啥：{prefs.get('note') or '无'}\n"
            "请基于以上信息写一句个性化推荐理由。"
        )
        try:
            result = await self._run_with_timeout(self._reason_agent, prompt)
            text = self._extract_text(result)
            text = (text or "").strip().strip('"').strip("「」").strip()
            cost_ms = (time.perf_counter() - start) * 1000
            self._log_ai("reason_writer", prompt, text, text,
                         cost_ms=cost_ms, success=True, fallback=False)
            return text or None
        except asyncio.TimeoutError:
            cost_ms = (time.perf_counter() - start) * 1000
            self._log_ai("reason_writer", prompt, "", None,
                         cost_ms=cost_ms, success=False, fallback=True, error=f"超时{settings.ai.ai_timeout}s")
            logger.warning("AI personalize_reason 超时(%ss)，回退默认 reason", settings.ai.ai_timeout)
            return None
        except Exception as e:
            cost_ms = (time.perf_counter() - start) * 1000
            self._log_ai("reason_writer", prompt, "", None,
                         cost_ms=cost_ms, success=False, fallback=True, error=str(e))
            logger.warning("AI personalize_reason 失败，回退默认 reason: %s", e)
            return None

    async def generate_sign(self, *, today_seed: int = 0) -> Optional[dict]:
        """AI3: 动态生成签文"""
        cfg = settings.ai.agent("sign_generator")
        if not cfg.enabled:
            return None

        import time
        start = time.perf_counter()
        prompt = "请生成一条今日签文。"
        try:
            result = await self._run_with_timeout(self._sign_agent, prompt)
            text = self._extract_text(result)
            data = self._safe_parse_json(text)
            cost_ms = (time.perf_counter() - start) * 1000
            if data and data.get("name") and data.get("text"):
                self._log_ai("sign_generator", prompt, text, data,
                             cost_ms=cost_ms, success=True, fallback=False)
                return {"name": data["name"], "level": data.get("level", "中签"), "text": data["text"]}
            self._log_ai("sign_generator", prompt, text, None,
                         cost_ms=cost_ms, success=False, fallback=True, error="返回数据不完整")
            return None
        except asyncio.TimeoutError:
            cost_ms = (time.perf_counter() - start) * 1000
            self._log_ai("sign_generator", prompt, "", None,
                         cost_ms=cost_ms, success=False, fallback=True, error=f"超时{settings.ai.ai_timeout}s")
            logger.warning("AI generate_sign 超时(%ss)，回退静态签池", settings.ai.ai_timeout)
            return None
        except Exception as e:
            cost_ms = (time.perf_counter() - start) * 1000
            self._log_ai("sign_generator", prompt, "", None,
                         cost_ms=cost_ms, success=False, fallback=True, error=str(e))
            logger.warning("AI generate_sign 失败，回退静态签池: %s", e)
            return None

    # ===== 内部工具 =====

    @staticmethod
    def _extract_text(result) -> str:
        """从 Runner.run 返回值中提取文本

        openai-agents 的结果对象 final_output 可能是 str 或 dict。
        """
        if result is None:
            return ""
        final = getattr(result, "final_output", None)
        if isinstance(final, str):
            return final
        if isinstance(final, dict):
            return json.dumps(final, ensure_ascii=False)
        return str(final) if final else ""

    @staticmethod
    def _safe_parse_json(text: str) -> Optional[dict]:
        """容错 JSON 解析

        LLM 输出常带 ```json 包裹或多余文本，这里尽力提取首个 {...} 块。
        """
        if not text:
            return None
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        start = text.find("{")
        end = text.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        return None
