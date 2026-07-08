"""AI 接入层

为选菜（pick_food）和签文生成（generate_sign）提供 AI 接入点。

设计原则：
1. 默认走 DummyProvider，零配置即可启动，不依赖任何外部服务
2. 通过配置启用 OpenAIAgentsProvider，使用 openai-agents SDK
3. 业务层只依赖 AIProvider 抽象接口，不感知具体实现
4. 所有 AI 调用都有超时/异常兜底，失败时回退到本地兜底逻辑

接入指南：
- 安装：pip install openai-agents
- 配置 .env：
    OPENAI_API_KEY=sk-xxx
    OPENAI_BASE_URL=https://api.openai.com/v1   # 可选，兼容代理
    OPENAI_MODEL=gpt-4o-mini
- 调用 get_ai_provider() 获取实例
"""
from app.ai.base import AIProvider
from app.ai.dummy import DummyProvider
from app.ai.factory import get_ai_provider

__all__ = ["AIProvider", "DummyProvider", "get_ai_provider"]
