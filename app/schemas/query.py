from typing import Any, Dict, List
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class SourceChunk(BaseModel):
    source: str | None = None
    doc_id: str | None = None
    chunk_index: int | None = None
    score: float
    preview: str


class QueryResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[SourceChunk]
    latency_ms: float
    retrieval_latency_ms: float
    llm_latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
