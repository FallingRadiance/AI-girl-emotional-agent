from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, START, END

from app.agent.skills import SKILLS, pick_skill
from app.agent.llm import structured_decision
from app.memory.store import store
from app.tools.builtin_tools import TOOL_REGISTRY, execute_tool


class AgentState(TypedDict, total=False):
    session_id: str
    user_message: str
    proactive: bool
    skill: str
    short_memory: List[Dict[str, str]]
    long_memory: List[Dict[str, str]]
    decision: Dict[str, Any]
    tool_name: Optional[str]
    tool_args: Dict[str, Any]
    tool_result: Optional[Dict[str, Any]]
    reply: str
    emotion: str


def build_tool_prompt() -> str:
    lines = []
    for name, info in TOOL_REGISTRY.items():
        lines.append(f"- {name}: {info['description']}; args={info['args']}")
    return "\n".join(lines)


def extract_long_memory(session_id: str, user_message: str) -> None:
    m = user_message.strip()
    if len(m) < 6:
        return
    for marker in ["我喜欢", "我讨厌", "我的目标是", "我叫", "我在"]:
        if marker in m:
            store.add_long(session_id, "user_fact", m)
            return


def format_tool_result(tool_name: Optional[str], result: Dict[str, Any]) -> str:
    if not result:
        return "我这次没有拿到有效的查询结果。"

    if not result.get("ok"):
        return f"这次查询失败了：{result.get('error', '未知错误')}。"

    if tool_name == "weather":
        city = result.get("city", "该城市")
        temp = result.get("temperature_c", "未知")
        hum = result.get("humidity", "未知")
        wind = result.get("wind_kmh", "未知")
        return f"{city}现在大约 {temp}°C，湿度 {hum}% ，风速约 {wind} km/h。"

    if tool_name == "datetime":
        return f"现在是 {result.get('human', '未知时间')}（{result.get('timezone', '')}）。"

    if tool_name == "news":
        items = result.get("items", [])[:3]
        if not items:
            return "我暂时没有拿到新闻数据。"
        lines = ["我看到这几条新闻："]
        for idx, item in enumerate(items, start=1):
            lines.append(f"{idx}. {item.get('title', '(无标题)')}")
        return "\n".join(lines)

    if tool_name == "math":
        return f"我算了一下，{result.get('expression', '')} = {result.get('result', '未知')}。"

    return "我已经查到了结果。"


async def node_decide(state: AgentState) -> AgentState:
    sid = state["session_id"]
    msg = state["user_message"]
    skill = pick_skill(msg)
    short_mem = store.list_short(sid, limit=12)
    long_mem = store.list_long(sid, limit=20)

    system_prompt = f"""
你是一个情感陪伴数字人主播，像虚拟主播一样自然亲切。
当前技能: {skill} - {SKILLS[skill]}
可用工具:\n{build_tool_prompt()}

你必须输出JSON，格式:
{{
  "reply": "给用户的话(中文，简洁自然)",
  "emotion": "happy|neutral|sad|angry|shy|surprised",
  "use_tool": true/false,
  "tool_name": "weather|datetime|news|math|null",
  "tool_args": {{}}
}}
规则:
1) 当用户明确需要事实信息时优先调用工具
2) 回复要体现陪伴感
3) 主动消息(proactive)时，语气轻柔，不要打扰感太强
""".strip()

    user_prompt = (
        f"proactive={state.get('proactive', False)}\n"
        f"user_message={msg}\n"
        f"short_memory={short_mem}\n"
        f"long_memory={long_mem}\n"
    )

    decision = await structured_decision(system_prompt, user_prompt)
    return {
        **state,
        "skill": skill,
        "short_memory": short_mem,
        "long_memory": long_mem,
        "decision": decision,
        "tool_name": decision.get("tool_name"),
        "tool_args": decision.get("tool_args") or {},
    }


def route_tool(state: AgentState) -> str:
    d = state.get("decision") or {}
    if d.get("use_tool") and d.get("tool_name") in TOOL_REGISTRY:
        return "call_tool"
    return "respond"


async def node_call_tool(state: AgentState) -> AgentState:
    name = state.get("tool_name")
    args = state.get("tool_args") or {}
    if not name:
        return {**state, "tool_result": {"ok": False, "error": "tool name missing"}}
    result = await execute_tool(name, args)
    return {**state, "tool_result": result}


async def node_respond(state: AgentState) -> AgentState:
    d = state.get("decision") or {}
    reply = d.get("reply") or "我在这儿陪你。"
    emotion = d.get("emotion") or "neutral"

    if state.get("tool_result"):
        tr = state["tool_result"]
        tool_name = state.get("tool_name")
        natural = format_tool_result(tool_name, tr)
        reply = f"{reply}\n\n{natural}"
        emotion = "surprised" if tr.get("ok") else "sad"

    return {**state, "reply": reply, "emotion": emotion}


async def node_update_memory(state: AgentState) -> AgentState:
    sid = state["session_id"]
    if not state.get("proactive"):
        store.append_short(sid, "user", state["user_message"])
    store.append_short(sid, "assistant", state.get("reply", ""))
    extract_long_memory(sid, state.get("user_message", ""))
    store.touch_agent(sid)
    return state


def compile_graph():
    g = StateGraph(AgentState)
    g.add_node("decide", node_decide)
    g.add_node("call_tool", node_call_tool)
    g.add_node("respond", node_respond)
    g.add_node("update_memory", node_update_memory)

    g.add_edge(START, "decide")
    g.add_conditional_edges("decide", route_tool, {"call_tool": "call_tool", "respond": "respond"})
    g.add_edge("call_tool", "respond")
    g.add_edge("respond", "update_memory")
    g.add_edge("update_memory", END)
    return g.compile()


agent_graph = compile_graph()


async def run_chat(session_id: str, message: str, proactive: bool = False) -> Dict[str, Any]:
    if not proactive:
        store.touch_user(session_id)
    state: AgentState = {
        "session_id": session_id,
        "user_message": message,
        "proactive": proactive,
    }
    out = await agent_graph.ainvoke(state)
    return {
        "reply": out.get("reply", "我在。"),
        "emotion": out.get("emotion", "neutral"),
        "skill": out.get("skill", "mood_booster"),
        "tool_used": out.get("tool_name"),
        "tool_result": out.get("tool_result"),
    }
