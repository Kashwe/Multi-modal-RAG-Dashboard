# import logging

# from fastapi import APIRouter, HTTPException

# from app.schemas.query import QueryRequest, QueryResponse, SourceChunk
# from app.services.analytics import analytics
# from app.services.qa_chain import answer_query
# from app.services.session_store import session_store

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/query", tags=["Query"])


# @router.post("/{session_id}", response_model=QueryResponse)
# async def query_session(session_id: str, body: QueryRequest) -> QueryResponse:
#     if session_store.get(session_id) is None:
#         raise HTTPException(status_code=404, detail="session not found")

#     try:
#         result = answer_query(session_id, body.question)
#     except Exception as exc:
#         logger.exception("QA chain failed: %s", exc)
#         raise HTTPException(status_code=500, detail=f"qa chain error: {exc}")

#     analytics.record_query(
#         session_id=session_id,
#         latency_ms=result["latency_ms"],
#         retrieval_scores=result["retrieval_scores"],
#         prompt_tokens=result["prompt_tokens"],
#         completion_tokens=result["completion_tokens"],
#     )

#     return QueryResponse(
#         session_id=session_id,
#         answer=result["answer"],
#         sources=[SourceChunk(**s) for s in result["sources"]],
#         latency_ms=result["latency_ms"],
#         retrieval_latency_ms=result["retrieval_latency_ms"],
#         llm_latency_ms=result["llm_latency_ms"],
#         prompt_tokens=result["prompt_tokens"],
#         completion_tokens=result["completion_tokens"],
#         total_tokens=result["prompt_tokens"] + result["completion_tokens"],
#     )








# import logging

# from fastapi import APIRouter, HTTPException

# from app.schemas.query import QueryRequest, QueryResponse, SourceChunk
# from app.services.analytics import analytics
# from app.services.qa_chain import answer_query
# from app.services.session_store import session_store

# # 🔐 RBAC
# from app.core.rbac import check_document_access

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/query", tags=["Query"])


# @router.post("/{session_id}", response_model=QueryResponse)
# async def query_session(session_id: str, body: QueryRequest) -> QueryResponse:

#     session = session_store.get(session_id)

#     if session is None:
#         raise HTTPException(status_code=404, detail="session not found")

#     try:
#         result = answer_query(session_id, body.question)
#     except Exception as exc:
#         logger.exception("QA chain failed: %s", exc)
#         raise HTTPException(status_code=500, detail=f"qa chain error: {exc}")

#     # 🔐 OPTIONAL SAFETY (if retrieval returns docs)
#     if "retrieved_docs" in result:
#         for doc in result["retrieved_docs"]:
#             check_document_access(doc, session)

#     analytics.record_query(
#         session_id=session_id,
#         latency_ms=result["latency_ms"],
#         retrieval_scores=result["retrieval_scores"],
#         prompt_tokens=result["prompt_tokens"],
#         completion_tokens=result["completion_tokens"],
#     )

#     return QueryResponse(
#         session_id=session_id,
#         answer=result["answer"],
#         sources=[SourceChunk(**s) for s in result["sources"]],
#         latency_ms=result["latency_ms"],
#         retrieval_latency_ms=result["retrieval_latency_ms"],
#         llm_latency_ms=result["llm_latency_ms"],
#         prompt_tokens=result["prompt_tokens"],
#         completion_tokens=result["completion_tokens"],
#         total_tokens=result["prompt_tokens"] + result["completion_tokens"],
#     )





# import logging

# from fastapi import APIRouter, HTTPException

# from app.schemas.query import QueryRequest, QueryResponse, SourceChunk
# from app.services.analytics import analytics
# from app.services.qa_chain import answer_query
# from app.services.session_store import session_store
# from app.core.rbac import require_role

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/query", tags=["Query"])


# @router.post("/{session_id}", response_model=QueryResponse)
# async def query_session(session_id: str, body: QueryRequest):

#     session = session_store.get(session_id)
#     if not session:
#         raise HTTPException(404, "session not found")

#     require_role(session, "user")

#     result = answer_query(session_id, body.question)

#     analytics.record_query(
#         session_id=session_id,
#         latency_ms=result["latency_ms"],
#         retrieval_scores=result["retrieval_scores"],
#         prompt_tokens=result["prompt_tokens"],
#         completion_tokens=result["completion_tokens"],
#     )

#     return QueryResponse(
#         session_id=session_id,
#         answer=result["answer"],
#         sources=[SourceChunk(**s) for s in result["sources"]],
#         latency_ms=result["latency_ms"],
#         retrieval_latency_ms=result["retrieval_latency_ms"],
#         llm_latency_ms=result["llm_latency_ms"],
#         prompt_tokens=result["prompt_tokens"],
#         completion_tokens=result["completion_tokens"],
#         total_tokens=result["prompt_tokens"] + result["completion_tokens"],
#     )





# import logging

# from fastapi import APIRouter, HTTPException

# from app.schemas.query import QueryRequest, QueryResponse, SourceChunk
# from app.services.analytics import analytics
# from app.services.qa_chain import answer_query
# from app.services.session_store import session_store
# from app.core.rbac import require_role

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/query", tags=["Query"])


# @router.post("/{session_id}", response_model=QueryResponse)
# async def query_session(session_id: str, body: QueryRequest):

#     session = session_store.get(session_id)

#     if not session:
#         raise HTTPException(404, "session not found")

#     require_role(session, "user")

#     # ✅ CHECK CACHE FIRST
#     cached = session_store.get_cache(session_id, body.question)

#     if cached:
#         logger.info("Cache hit for question: %s", body.question)
#         return QueryResponse(**cached)

#     logger.info("Cache miss for question: %s", body.question)

#     # ✅ RUN QA CHAIN
#     result = answer_query(session_id, body.question)

#     analytics.record_query(
#         session_id=session_id,
#         latency_ms=result["latency_ms"],
#         retrieval_scores=result["retrieval_scores"],
#         prompt_tokens=result["prompt_tokens"],
#         completion_tokens=result["completion_tokens"],
#     )

#     # ✅ RESPONSE PAYLOAD
#     response_payload = {
#         "session_id": session_id,
#         "answer": result["answer"],
#         "sources": result["sources"],
#         "latency_ms": result["latency_ms"],
#         "retrieval_latency_ms": result["retrieval_latency_ms"],
#         "llm_latency_ms": result["llm_latency_ms"],
#         "prompt_tokens": result["prompt_tokens"],
#         "completion_tokens": result["completion_tokens"],
#         "total_tokens": result["prompt_tokens"] + result["completion_tokens"],
#     }

#     # ✅ SAVE CACHE
#     session_store.set_cache(
#         session_id,
#         body.question,
#         response_payload
#     )

#     return QueryResponse(**response_payload)






import logging

from fastapi import APIRouter, HTTPException

from app.schemas.query import QueryRequest, QueryResponse
from app.services.analytics import analytics
from app.services.qa_chain import answer_query
from app.services.session_store import session_store
from app.core.rbac import require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/{session_id}", response_model=QueryResponse)
async def query_session(session_id: str, body: QueryRequest):

    session = session_store.get(session_id)

    if not session:
        raise HTTPException(404, "session not found")

    require_role(session, "user")

    cache_key = (
        f"{body.question}::{body.comparison_mode}"
    )

    cached = session_store.get_cache(
        session_id,
        cache_key
    )

    if cached:
        logger.info(
            "Cache hit for question: %s",
            body.question
        )
        return QueryResponse(**cached)

    logger.info(
        "Cache miss for question: %s",
        body.question
    )

    result = answer_query(
        session_id=session_id,
        question=body.question,
        comparison_mode=body.comparison_mode,
    )

    analytics.record_query(
        session_id=session_id,
        latency_ms=result["latency_ms"],
        retrieval_scores=result["retrieval_scores"],
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
    )

    response_payload = {
        "session_id": session_id,
        "answer": result["answer"],
        "sources": result["sources"],
        "comparison_sources": result[
            "comparison_sources"
        ],
        "comparison_mode": result[
            "comparison_mode"
        ],
        "latency_ms": result["latency_ms"],
        "retrieval_latency_ms": result[
            "retrieval_latency_ms"
        ],
        "llm_latency_ms": result[
            "llm_latency_ms"
        ],
        "prompt_tokens": result[
            "prompt_tokens"
        ],
        "completion_tokens": result[
            "completion_tokens"
        ],
        "total_tokens": (
            result["prompt_tokens"]
            + result["completion_tokens"]
        ),
    }

    session_store.set_cache(
        session_id,
        cache_key,
        response_payload
    )

    return QueryResponse(**response_payload)