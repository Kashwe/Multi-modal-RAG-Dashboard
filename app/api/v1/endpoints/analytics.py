from fastapi import APIRouter, HTTPException

from app.services.analytics import analytics
from app.services.session_store import session_store

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/latency")
async def latency_metrics():
    return analytics.latency_summary()


@router.get("/retrieval")
async def retrieval_metrics():
    return analytics.retrieval_summary()


@router.get("/tokens")
async def token_metrics():
    return analytics.token_summary()


@router.get("/summary")
async def summary_metrics():
    return {
        "latency": analytics.latency_summary(),
        "retrieval": analytics.retrieval_summary(),
        "tokens": analytics.token_summary(),
        "sessions": {
            "backend": session_store.backend,
            "active": len(session_store.list_ids()),
        },
    }


@router.get("/sessions/{session_id}")
async def session_metrics(session_id: str):
    payload = session_store.get(session_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="session not found")
    latencies = payload.get("latencies_ms", [])
    scores = payload.get("retrieval_scores", [])
    return {
        "session_id": session_id,
        "message_count": payload.get("message_count", 0),
        "tokens": payload.get("tokens", {"prompt": 0, "completion": 0, "total": 0}),
        "latency": {
            "count": len(latencies),
            "avg_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
            "samples": [round(x, 2) for x in latencies[-50:]],
        },
        "retrieval": {
            "count": len(scores),
            "avg": round(sum(scores) / len(scores), 4) if scores else 0.0,
            "samples": [round(x, 4) for x in scores[-50:]],
        },
    }
