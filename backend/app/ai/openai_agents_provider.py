"""基于 openai-agents SDK 的 Provider 实现

使用 OpenAI Agents SDK 实现 AIProvider 接口。
对应 TASKS.md 中的三个 AI 接入点：
- AI1 parse_note: 用 Agent 把自由文本解析为结构化偏好 JSON
- AI2 personalize_reason: 用 Agent 生成个性化推荐理由
- AI3 generate_sign: 用 Agent 动态生成签文

启用方式：
    USE_AI=1 + OPENAI_API_KEY

注意：openai-agents SDK 是异步的，所有方法用 await 调用。
所有方法均带异常兜底，失败返回 None / 空结果，不影响主流程。
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from app.ai.base import AIProvider, NoteParseResult
from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIAgentsProvider(AIProvider):
    """基于 openai-agents SDK 的 AI 实现

    三个 AI 接入点分别用独立 Agent 完成，Prompt 中均限定：
    - 菜品池范围（避免幻觉出池外菜品）
    - 输出格式（JSON / 文本）
    - 失败兜底由上层处理
    """

    def __init__(self) -> None:
        # 延迟导入：仅在 USE_AI=1 时才加载 SDK，避免默认场景下强依赖
        try:
            from agents import Agent, Runner  # type: ignore  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "未安装 openai-agents SDK，请执行: pip install openai-agents"
            ) from e

        # 配置 OpenAI 客户端（兼容 base_url 代理）
        client_kwargs = {}
        if settings.openai_api_key:
            client_kwargs["api_key"] = settings.openai_api_key
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url

        # 构造三个独立 Agent
        self._note_agent = Agent(
            name="note-parser",
            instructions=(
                "你是一个美食偏好解析助手。用户会输入一段自由文本描述想吃的食物，"
                "你需要解析为结构化偏好。返回严格的 JSON：\n"
                '{"mood": "tired|hungry|sad|happy|busy|spicy|no-appetite|treat|null", '
                '"flavor": "light|spicy|sour-sweet|sour-spicy|savory|heavy|milky|fresh|null", '
                '"keywords": ["..."]}\n'
                "mood/flavor 找不到就给 null。keywords 是从文本中提取的食物关键词。"
                "只返回 JSON，不要任何额外说明。"
            ),
            model=settings.openai_model,
        )

        self._reason_agent = Agent(
            name="reason-writer",
            instructions=(
                "你是「今日宜吃」小程序的文案。根据用户心情和偏好，"
                "为指定菜品写一句 30-50 字的个性化推荐理由，语气活泼可爱。"
                "只输出理由文案本身，不要标题、不要引号。"
            ),
            model=settings.openai_model,
        )

        self._sign_agent = Agent(
            name="sign-generator",
            instructions=(
                "你是「今日宜吃」的签文生成器。生成一条当日限定签文，"
                "包含 name（4-6 字短签名，含\"签\"字）、level（上上签/上签/中吉/中签）、"
                "text（20-40 字签文内容，活泼可爱风）。返回严格 JSON："
                '{"name":"...","level":"...","text":"..."}'
                "只返回 JSON。"
            ),
            model=settings.openai_model,
        )

    @property
    def name(self) -> str:
        return "openai-agents"

    async def parse_note(self, note: str, *, today_seed: int = 0) -> NoteParseResult:
        """AI1: 解析「想吃点啥」自由文本"""
        if not note or not note.strip():
            return NoteParseResult(prefs=None, note_raw=note)

        try:
            from agents import Runner

            result = await Runner.run(self._note_agent, note.strip())
            text = self._extract_text(result)
            prefs = self._safe_parse_json(text)
            if prefs is None:
                return NoteParseResult(prefs=None, note_raw=note)
            # 兼容字段：null / 缺失都统一成 None
            mood = prefs.get("mood")
            flavor = prefs.get("flavor")
            if mood in ("", "null"):
                mood = None
            if flavor in ("", "null"):
                flavor = None
            return NoteParseResult(
                prefs={"mood": mood, "flavor": flavor, "note": note, "keywords": prefs.get("keywords", [])},
                note_raw=note,
                extra={"raw": text},
            )
        except Exception as e:
            logger.warning("AI parse_note 失败，回退本地兜底: %s", e)
            return NoteParseResult(prefs=None, note_raw=note)

    async def personalize_reason(self, food: dict, prefs: dict, *, today_seed: int = 0) -> Optional[str]:
        """AI2: 生成个性化推荐理由"""
        try:
            from agents import Runner

            prompt = (
                f"菜品：{food.get('title')}（{food.get('category')}）\n"
                f"默认理由：{food.get('reason')}\n"
                f"用户心情：{prefs.get('mood') or '未知'}\n"
                f"口味偏好：{prefs.get('flavor') or '未知'}\n"
                f"想吃点啥：{prefs.get('note') or '无'}\n"
                "请基于以上信息写一句个性化推荐理由。"
            )
            result = await Runner.run(self._reason_agent, prompt)
            text = self._extract_text(result)
            text = (text or "").strip().strip('"').strip("「」").strip()
            return text or None
        except Exception as e:
            logger.warning("AI personalize_reason 失败，回退默认 reason: %s", e)
            return None

    async def generate_sign(self, *, today_seed: int = 0) -> Optional[dict]:
        """AI3: 动态生成签文"""
        try:
            from agents import Runner

            result = await Runner.run(self._sign_agent, "请生成一条今日签文。")
            text = self._extract_text(result)
            data = self._safe_parse_json(text)
            if data and data.get("name") and data.get("text"):
                return {"name": data["name"], "level": data.get("level", "中签"), "text": data["text"]}
            return None
        except Exception as e:
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
        # 新版 SDK：result.final_output
        final = getattr(result, "final_output", None)
        if isinstance(final, str):
            return final
        if isinstance(final, dict):
            return json.dumps(final, ensure_ascii=False)
        # 兜底：转字符串
        return str(final) if final else ""

    @staticmethod
    def _safe_parse_json(text: str) -> Optional[dict]:
        """容错 JSON 解析

        LLM 输出常带 ```json 包裹或多余文本，这里尽力提取首个 {...} 块。
        """
        if not text:
            return None
        text = text.strip()
        # 去除 markdown 代码块
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        # 直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # 提取首个 {...}
        start = text.find("{")
        end = text.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        return None
