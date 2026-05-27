import threading
import time
from collections import deque
from statistics import mean
from typing import Deque, Dict, List

from app.services.session_store import session_store


class AnalyticsStore:
    """
    Lightweight in-process analytics aggregator. Per-session detail lives
    in the session payload; this class keeps a global rolling window for
    the dashboard summary endpoints.
    """

    MAX_SAMPLES = 500

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._latencies: Deque[float] = deque(maxlen=self.MAX_SAMPLES)
        self._retrieval_scores: Deque[float] = deque(maxlen=self.MAX_SAMPLES)
        self._token_events: Deque[Dict[str, int]] = deque(maxlen=self.MAX_SAMPLES)

    def record_query(
        self,
        session_id: str,
        latency_ms: float,
        retrieval_scores: List[float],
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        with self._lock:
            self._latencies.append(latency_ms)
            for s in retrieval_scores:
                self._retrieval_scores.append(s)
            self._token_events.append(
                {
                    "prompt": prompt_tokens,
                    "completion": completion_tokens,
                    "total": prompt_tokens + completion_tokens,
                    "ts": int(time.time()),
                }
            )

        session_store.append(session_id, "latencies_ms", latency_ms)
        for s in retrieval_scores:
            session_store.append(session_id, "retrieval_scores", s)
        session_store.add_tokens(session_id, prompt_tokens, completion_tokens)

    def latency_summary(self) -> Dict[str, float]:
        with self._lock:
            samples = list(self._latencies)
        if not samples:
            return {"count": 0, "avg_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0}
        ordered = sorted(samples)
        return {
            "count": len(ordered),
            "avg_ms": round(mean(ordered), 2),
            "p50_ms": round(ordered[len(ordered) // 2], 2),
            "p95_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 2),
            "max_ms": round(ordered[-1], 2),
            "samples": [round(s, 2) for s in samples[-50:]],
        }

    def retrieval_summary(self) -> Dict[str, object]:
        with self._lock:
            samples = list(self._retrieval_scores)
        if not samples:
            return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0, "histogram": []}
        buckets = [0] * 10
        for s in samples:
            idx = min(int(s * 10), 9) if 0 <= s <= 1 else 9
            buckets[idx] += 1
        return {
            "count": len(samples),
            "avg": round(mean(samples), 4),
            "min": round(min(samples), 4),
            "max": round(max(samples), 4),
            "histogram": [
                {"bucket": f"{i/10:.1f}-{(i+1)/10:.1f}", "count": c}
                for i, c in enumerate(buckets)
            ],
            "samples": [round(s, 4) for s in samples[-50:]],
        }

    def token_summary(self) -> Dict[str, object]:
        with self._lock:
            events = list(self._token_events)
        if not events:
            return {
                "queries": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "avg_per_query": 0.0,
                "recent": [],
            }
        total_prompt = sum(e["prompt"] for e in events)
        total_completion = sum(e["completion"] for e in events)
        total_all = total_prompt + total_completion
        return {
            "queries": len(events),
            "prompt_tokens": total_prompt,
            "completion_tokens": total_completion,
            "total_tokens": total_all,
            "avg_per_query": round(total_all / len(events), 2),
            "recent": events[-20:],
        }


analytics = AnalyticsStore()
