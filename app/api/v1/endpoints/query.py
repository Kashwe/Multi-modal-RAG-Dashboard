import logging

from fastapi import APIRouter, HTTPException

from app.schemas.query import QueryRequest, QueryResponse, SourceChunk
from app.services.analytics import analytics
from app.services.qa_chain import answer_query
from app.services.session_store import session_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/{session_id}", response_model=QueryResponse)
async def query_session(session_id: str, body: QueryRequest) -> QueryResponse:
    if session_store.get(session_id) is None:
        raise HTTPException(status_code=404, detail="session not found")

    try:
        result = answer_query(session_id, body.question)
    except Exception as exc:
        logger.exception("QA chain failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"qa chain error: {exc}")

    analytics.record_query(
        session_id=session_id,
        latency_ms=result["latency_ms"],
        retrieval_scores=result["retrieval_scores"],
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
    )

    return QueryResponse(
        session_id=session_id,
        answer=result["answer"],
        sources=[SourceChunk(**s) for s in result["sources"]],
        latency_ms=result["latency_ms"],
        retrieval_latency_ms=result["retrieval_latency_ms"],
        llm_latency_ms=result["llm_latency_ms"],
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
        total_tokens=result["prompt_tokens"] + result["completion_tokens"],
    )
