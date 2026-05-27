from typing import List, Dict, Optional
from pydantic import BaseModel


class SessionCreateResponse(BaseModel):
    session_id: str
    backend: str


class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0
    total: int = 0


class SessionInfo(BaseModel):
    session_id: str
    created_at: float
    last_seen: float
    doc_ids: List[str] = []
    message_count: int = 0
    tokens: TokenUsage = TokenUsage()


class SessionListResponse(BaseModel):
    backend: str
    count: int
    session_ids: List[str]
