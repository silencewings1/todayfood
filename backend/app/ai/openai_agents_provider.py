"""基于 openai-agents SDK 的 Provider 实现

使用 OpenAI Agents SDK 实现 AIProvider 接口，支持两种 API 协议：
- chat_completions: POST /v1/chat/completions（兼容 OpenAI 官方 + 绝大多数第三方服务）
- responses:        POST /v1/responses（OpenAI 官方新协议）

协议通过 config/ai.toml 的 ai.api_protocol 字段切换，也支持环境变量 AI_PROTOCOL 覆盖。

AI 接入点：
- pick_food:      food_picker agent，结合黄历推荐菜品（含理由+做法+食材+步骤）
- generate_sign:  sign_generator agent，动态生成签文（可选，默认禁用）

每个 agent 可在 ai.toml 中独立开关、配置模型与温度。
所有方法均带异常兜底，失败返回 None，不影响主流程。
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from app.ai.base import AIProvider
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

        # 构造 food_picker agent（核心：选菜+理由+做法）
        self._food_picker_agent = self._build_agent(
            name="food-picker",
            agent_key="food_picker",
            instructions=(
                "你是「今日宜吃」的 AI 厨师，负责结合黄历为用户推荐一道菜。\n"
                "你需要返回严格的 JSON，字段如下：\n"
                '{\n'
                '  "title": "菜品名（2-8字）",\n'
                '  "category": "分类（主食/汤面/小炒/凉菜/甜品/饮品类之一）",\n'
                '  "reason": "推荐理由（30-60字，结合黄历宜忌和用户偏好，活泼可爱）",\n'
                '  "cookTime": "烹饪时长（如 30 分钟）",\n'
                '  "difficulty": "难度（简单/中等/偏难）",\n'
                '  "ingredients": ["食材1 用量", "食材2 用量", ...],\n'
                '  "steps": ["步骤1", "步骤2", ...],\n'
                '  "tip": "一个小贴士（10-30字）"\n'
                '}\n'
                "要求：\n"
                "1. 菜品要结合黄历宜忌（如宜辛辣就推荐辣菜，忌油腻就推荐清淡的）\n"
                "2. 食材用量要具体（如 番茄 2个、鸡蛋 3个）\n"
                "3. 步骤 4-8 步，每步简明扼要\n"
                "4. 不要推荐与 exclude_title 相同的菜\n"
                "5. 只返回 JSON，不要任何额外说明"
            ),
            model_cls=model_cls,
        )

        # 构造 sign_generator agent（可选：动态签文）
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
        """构造单个 Agent（读取 ai.toml 中对应 agent 配置）"""
        from agents import Agent, ModelSettings

        cfg = settings.ai.agent(agent_key)
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
        """带超时地执行 Agent"""
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
            pass

    async def pick_food(self, context: dict, *, today_seed: int = 0) -> Optional[dict]:
        """AI 选菜（含理由 + 做法 + 黄历结合）"""
        cfg = settings.ai.agent("food_picker")
        if not cfg.enabled:
            return None

        import time
        start = time.perf_counter()

        # 构造 prompt，把黄历上下文和用户偏好都传给 AI
        lines = [
            f"今日日期：{context.get('date_text', '')}",
            f"农历：{context.get('lunar_text', '')}",
            f"黄历宜：{'、'.join(context.get('almanac_yi', []))}",
            f"黄历忌：{'、'.join(context.get('almanac_ji', []))}",
            f"幸运口味：{context.get('lucky_flavor', '')}",
            f"幸运颜色：{context.get('lucky_color', '')}",
            f"食神方位：{context.get('lucky_direction', '')}",
        ]
        mood = context.get('mood')
        flavor = context.get('flavor')
        note = context.get('note')
        if mood:
            lines.append(f"用户心情：{mood}")
        if flavor:
            lines.append(f"口味偏好：{flavor}")
        if note:
            lines.append(f"想吃点啥：{note}")
        exclude = context.get('exclude_title')
        if exclude:
            lines.append(f"排除菜品（不要推荐相同的）：{exclude}")
        lines.append("请结合以上黄历信息推荐一道菜，返回 JSON。")
        prompt = "\n".join(lines)

        try:
            result = await self._run_with_timeout(self._food_picker_agent, prompt)
            text = self._extract_text(result)
            data = self._safe_parse_json(text)
            cost_ms = (time.perf_counter() - start) * 1000

            if not data or not data.get("title"):
                self._log_ai("food_picker", prompt, text, None,
                             cost_ms=cost_ms, success=False, fallback=True, error="返回数据不完整")
                return None

            # 补全 FoodItem 所需的全部字段
            title = data["title"]
            food = {
                "id": title.replace(" ", "-").lower(),
                "title": title,
                "category": data.get("category", "主食"),
                "tags": {"mood": [], "scene": [], "budget": [], "flavor": []},
                "stars": [4, 5, 5],
                "reason": data.get("reason", "今日推荐"),
                "sign": "",
                "signName": "",
                "level": "",
                "luckyFlavor": context.get("lucky_flavor", ""),
                "luckyColor": context.get("lucky_color", ""),
                "direction": context.get("lucky_direction", ""),
                "cookTime": data.get("cookTime", ""),
                "difficulty": data.get("difficulty", "简单"),
                "ingredients": data.get("ingredients", []),
                "steps": data.get("steps", []),
                "tip": data.get("tip", ""),
            }

            self._log_ai("food_picker", prompt, text, food,
                         cost_ms=cost_ms, success=True, fallback=False)
            return food

        except asyncio.TimeoutError:
            cost_ms = (time.perf_counter() - start) * 1000
            self._log_ai("food_picker", prompt, "", None,
                         cost_ms=cost_ms, success=False, fallback=True, error=f"超时{settings.ai.ai_timeout}s")
            logger.warning("AI pick_food 超时(%ss)，回退本地选菜", settings.ai.ai_timeout)
            return None
        except Exception as e:
            cost_ms = (time.perf_counter() - start) * 1000
            self._log_ai("food_picker", prompt, "", None,
                         cost_ms=cost_ms, success=False, fallback=True, error=str(e))
            logger.warning("AI pick_food 失败，回退本地选菜: %s", e)
            return None

    async def generate_sign(self, *, today_seed: int = 0) -> Optional[dict]:
        """动态生成签文（可选功能）"""
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
        """从 Runner.run 返回值中提取文本"""
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
        """容错 JSON 解析（LLM 输出常带 ```json 包裹或多余文本）"""
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
