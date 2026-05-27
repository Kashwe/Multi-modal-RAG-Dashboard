import logging
import threading
import time
from typing import Any, Dict, List

from app.core.config import settings
from app.services.vector_store import vector_store_manager

logger = logging.getLogger(__name__)

_llm = None
_llm_lock = threading.Lock()
_tokenizer = None


def _get_llm():
    global _llm
    if _llm is not None:
        return _llm
    with _llm_lock:
        if _llm is not None:
            return _llm
        from langchain_groq import ChatGroq

        _llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=0.2,
        )
        logger.info("Groq LLM initialized: model=%s", settings.GROQ_MODEL)
        return _llm


def _count_tokens(text: str) -> int:
    global _tokenizer
    if _tokenizer is None:
        try:
            import tiktoken

            _tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _tokenizer = False
    if _tokenizer:
        return len(_tokenizer.encode(text))
    return max(1, len(text) // 4)


SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions strictly from the provided "
    "context. If the answer is not in the context, say you don't know. Cite the "
    "source filenames when relevant. Keep answers concise."
)


def _format_context(docs_with_scores) -> str:
    lines = []
    for i, (doc, _score) in enumerate(docs_with_scores, start=1):
        src = doc.metadata.get("source", "unknown")
        lines.append(f"[{i}] (source: {src})\n{doc.page_content}")
    return "\n\n".join(lines)


def _normalize_score(raw: float) -> float:
    # FAISS returns L2 distance for normalized embeddings; convert to a
    # 0-1 similarity score for the analytics dashboard.
    sim = 1.0 - (raw / 2.0)
    return max(0.0, min(1.0, sim))


def answer_query(session_id: str, question: str) -> Dict[str, Any]:
    """
    Run the full RAG query: retrieve, prompt, call LLM, measure.

    Returns a dict with answer, sources, latency_ms, retrieval_scores,
    and token usage so the endpoint can record analytics in one place.
    """
    started = time.perf_counter()

    results = vector_store_manager.search(session_id, question)
    retrieval_latency_ms = (time.perf_counter() - started) * 1000.0
    retrieval_scores = [_normalize_score(float(score)) for _doc, score in results]

    if not results:
        total_ms = (time.perf_counter() - started) * 1000.0
        return {
            "answer": "No documents have been indexed for this session yet.",
            "sources": [],
            "retrieval_scores": [],
            "retrieval_latency_ms": round(retrieval_latency_ms, 2),
            "llm_latency_ms": 0.0,
            "latency_ms": round(total_ms, 2),
            "prompt_tokens": 0,
            "completion_tokens": 0,
        }

    context = _format_context(results)
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    llm = _get_llm()
    llm_started = time.perf_counter()
    response = llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )
    llm_latency_ms = (time.perf_counter() - llm_started) * 1000.0
    answer = getattr(response, "content", str(response))

    usage = getattr(response, "usage_metadata", None) or {}
    prompt_tokens = int(
        usage.get("input_tokens")
        or usage.get("prompt_tokens")
        or _count_tokens(SYSTEM_PROMPT + user_prompt)
    )
    completion_tokens = int(
        usage.get("output_tokens")
        or usage.get("completion_tokens")
        or _count_tokens(answer)
    )

    sources: List[Dict[str, Any]] = []
    for (doc, _score), sim in zip(results, retrieval_scores):
        sources.append(
            {
                "source": doc.metadata.get("source"),
                "doc_id": doc.metadata.get("doc_id"),
                "chunk_index": doc.metadata.get("chunk_index"),
                "score": round(sim, 4),
                "preview": doc.page_content[:200],
            }
        )

    total_ms = (time.perf_counter() - started) * 1000.0
    return {
        "answer": answer,
        "sources": sources,
        "retrieval_scores": retrieval_scores,
        "retrieval_latency_ms": round(retrieval_latency_ms, 2),
        "llm_latency_ms": round(llm_latency_ms, 2),
        "latency_ms": round(total_ms, 2),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
