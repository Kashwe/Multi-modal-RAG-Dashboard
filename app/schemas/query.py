# from typing import Any, Dict, List
# from pydantic import BaseModel, Field


# class QueryRequest(BaseModel):
#     question: str = Field(..., min_length=1, max_length=2000)


# class SourceChunk(BaseModel):
#     source: str | None = None
#     doc_id: str | None = None
#     chunk_index: int | None = None
#     score: float
#     preview: str


# class QueryResponse(BaseModel):
#     session_id: str
#     answer: str
#     sources: List[SourceChunk]
#     latency_ms: float
#     retrieval_latency_ms: float
#     llm_latency_ms: float
#     prompt_tokens: int
#     completion_tokens: int
#     total_tokens: int




# from typing import List
# from pydantic import BaseModel, Field


# class QueryRequest(BaseModel):
#     question: str = Field(..., min_length=1, max_length=2000)


# class CompareQueryRequest(BaseModel):
#     question: str = Field(..., min_length=1, max_length=2000)

#     doc_ids: List[str] = Field(
#         ...,
#         min_items=2,
#         description="List of document IDs to compare"
#     )


# class SourceChunk(BaseModel):
#     source: str | None = None
#     doc_id: str | None = None
#     chunk_index: int | None = None
#     score: float
#     preview: str


# class QueryResponse(BaseModel):
#     session_id: str
#     answer: str
#     sources: List[SourceChunk]
#     latency_ms: float
#     retrieval_latency_ms: float
#     llm_latency_ms: float
#     prompt_tokens: int
#     completion_tokens: int
#     total_tokens: int


# class CompareQueryResponse(BaseModel):
#     session_id: str
#     answer: str
#     compared_documents: int
#     sources: List[SourceChunk]
#     latency_ms: float
#     retrieval_latency_ms: float
#     llm_latency_ms: float
#     prompt_tokens: int
#     completion_tokens: int
#     total_tokens: int




from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

    # ✅ US322
    comparison_mode: bool = False


class SourceChunk(BaseModel):
    source: str | None = None
    doc_id: str | None = None
    chunk_index: int | None = None
    score: float
    preview: str


# ✅ US322
class ComparisonSource(BaseModel):
    document: str
    chunks: List[SourceChunk]


class QueryResponse(BaseModel):
    session_id: str

    answer: str

    sources: List[SourceChunk]

    # ✅ US322
    comparison_sources: Optional[List[ComparisonSource]] = None

    # ✅ US322
    comparison_mode: bool = False

    latency_ms: float
    retrieval_latency_ms: float
    llm_latency_ms: float

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int