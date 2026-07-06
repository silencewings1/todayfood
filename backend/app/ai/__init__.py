"""AI 接入层

为后续 AI1（note 自由文本解析）、AI2（推荐理由个性化）、AI3（签文动态生成）预留接入点。

设计原则：
1. 默认走 DummyProvider，零配置即可启动，不依赖任何外部服务
2. 通过环境变量 USE_AI=1 切换到 OpenAIAgentsProvider，使用 openai-agents SDK
3. 业务层只依赖 AIProvider 抽象接口，不感知具体实现
4. 所有 AI 调用都有超时/异常兜底，失败时回退到本地兜底逻辑

接入指南：
- 安装：pip install openai-agents
- 配置 .env：
    USE_AI=1
    OPENAI_API_KEY=sk-xxx
    OPENAI_BASE_URL=https://api.openai.com/v1   # 可选，兼容代理
    OPENAI_MODEL=gpt-4o-mini
- 调用 get_ai_provider() 获取实例
"""
from app.ai.base import AIProvider, NoteParseResult
from app.ai.dummy import DummyProvider
from app.ai.factory import get_ai_provider

__all__ = ["AIProvider", "NoteParseResult", "DummyProvider", "get_ai_provider"]
