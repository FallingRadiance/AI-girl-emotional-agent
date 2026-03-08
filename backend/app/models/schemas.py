from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str
    emotion: str
    skill: str
    tool_used: Optional[str] = None
    tool_result: Optional[Any] = None


class MemorySnapshot(BaseModel):
    session_id: str
    short_term: List[Dict[str, str]]
    long_term: List[Dict[str, str]]


class ProactiveResponse(BaseModel):
    has_message: bool
    reply: Optional[str] = None
    emotion: Optional[str] = None
    skill: Optional[str] = None
