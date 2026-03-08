import json
from typing import Any, Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings


def has_llm() -> bool:
    return bool(settings.deepseek_api_key)


def build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.7,
    )


async def structured_decision(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    if not has_llm():
        # Fallback when no key yet.
        return {
            "reply": f"我收到了：{user_prompt[:120]}。我在认真听你说，也愿意继续陪你聊。",
            "emotion": "neutral",
            "use_tool": False,
            "tool_name": None,
            "tool_args": {},
        }

    llm = build_llm()
    res = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    text = res.content if isinstance(res.content, str) else str(res.content)
    try:
        return json.loads(text)
    except Exception:
        return {
            "reply": text,
            "emotion": "neutral",
            "use_tool": False,
            "tool_name": None,
            "tool_args": {},
        }
