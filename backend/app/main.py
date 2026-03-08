from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import run_chat
from app.memory.store import store
from app.models.schemas import ChatRequest, ChatResponse, MemorySnapshot, ProactiveResponse
from app.tools.builtin_tools import TOOL_REGISTRY

app = FastAPI(title="AI Girl Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/tools")
async def tools():
    return {
        "tools": [
            {"name": k, "description": v["description"], "args": v["args"]}
            for k, v in TOOL_REGISTRY.items()
        ]
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    out = await run_chat(req.session_id, req.message, proactive=False)
    return ChatResponse(**out)


@app.get("/memory/{session_id}", response_model=MemorySnapshot)
async def memory(session_id: str):
    return MemorySnapshot(
        session_id=session_id,
        short_term=store.list_short(session_id, limit=30),
        long_term=store.list_long(session_id, limit=50),
    )


@app.get("/proactive/{session_id}", response_model=ProactiveResponse)
async def proactive(session_id: str):
    threshold_seconds = 30
    if not store.should_trigger_proactive(session_id, threshold_seconds):
        return ProactiveResponse(has_message=False)

    out = await run_chat(
        session_id,
        "用户已经超过30秒没有说话，请你主动轻声开启一个新话题或关心对方。",
        proactive=True,
    )
    store.mark_proactive_sent(session_id)
    return ProactiveResponse(
        has_message=True,
        reply=out["reply"],
        emotion=out["emotion"],
        skill=out["skill"],
    )
