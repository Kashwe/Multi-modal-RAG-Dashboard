import json
import logging
import threading
import time
import uuid
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class _InMemoryStore:
    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
        self._expiry: Dict[str, float] = {}
        self._lock = threading.RLock()

    def _purge(self, key: str) -> None:
        if key in self._expiry and self._expiry[key] < time.time():
            self._data.pop(key, None)
            self._expiry.pop(key, None)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            self._purge(key)
            return self._data.get(key)

    def set(self, key: str, value: Dict[str, Any], ttl: int) -> None:
        with self._lock:
            self._data[key] = value
            self._expiry[key] = time.time() + ttl

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)
            self._expiry.pop(key, None)

    def keys(self, prefix: str) -> list[str]:
        with self._lock:
            return [k for k in list(self._data.keys()) if k.startswith(prefix)]


class SessionStore:
    """
    Session store with Redis backend and in-memory fallback.

    Stores per-session metadata: created_at, last_seen, doc_ids, message_count,
    plus analytics counters (token usage, latency samples, retrieval scores).
    """

    SESSION_PREFIX = "session:"

    def __init__(self) -> None:
        self._memory = _InMemoryStore()
        self._redis = None
        self._connect_redis()

    def _connect_redis(self) -> None:
        try:
            import redis  # type: ignore

            client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            client.ping()
            self._redis = client
            logger.info("Session store connected to Redis at %s", settings.REDIS_URL)
        except Exception as exc:
            self._redis = None
            logger.warning(
                "Redis unavailable (%s); using in-memory session store", exc
            )

    @property
    def backend(self) -> str:
        return "redis" if self._redis is not None else "memory"

    def _key(self, session_id: str) -> str:
        return f"{self.SESSION_PREFIX}{session_id}"

    def create(self) -> str:
        session_id = uuid.uuid4().hex
        now = time.time()
        payload = {
            "session_id": session_id,
            "created_at": now,
            "last_seen": now,
            "doc_ids": [],
            "message_count": 0,
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "latencies_ms": [],
            "retrieval_scores": [],
        }
        self._write(session_id, payload)
        return session_id

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self._redis is not None:
            raw = self._redis.get(self._key(session_id))
            if raw is None:
                return None
            return json.loads(raw)
        return self._memory.get(self._key(session_id))

    def _write(self, session_id: str, payload: Dict[str, Any]) -> None:
        payload["last_seen"] = time.time()
        if self._redis is not None:
            self._redis.set(
                self._key(session_id), json.dumps(payload), ex=settings.SESSION_TTL
            )
        else:
            self._memory.set(self._key(session_id), payload, settings.SESSION_TTL)

    def update(self, session_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
        payload = self.get(session_id)
        if payload is None:
            return None
        payload.update(fields)
        self._write(session_id, payload)
        return payload

    def append(self, session_id: str, field: str, value: Any) -> Optional[Dict[str, Any]]:
        payload = self.get(session_id)
        if payload is None:
            return None
        payload.setdefault(field, []).append(value)
        self._write(session_id, payload)
        return payload

    def add_tokens(
        self, session_id: str, prompt: int, completion: int
    ) -> Optional[Dict[str, Any]]:
        payload = self.get(session_id)
        if payload is None:
            return None
        tokens = payload.setdefault(
            "tokens", {"prompt": 0, "completion": 0, "total": 0}
        )
        tokens["prompt"] += prompt
        tokens["completion"] += completion
        tokens["total"] = tokens["prompt"] + tokens["completion"]
        payload["message_count"] = payload.get("message_count", 0) + 1
        self._write(session_id, payload)
        return payload

    def delete(self, session_id: str) -> bool:
        key = self._key(session_id)
        if self._redis is not None:
            return bool(self._redis.delete(key))
        existed = self._memory.get(key) is not None
        self._memory.delete(key)
        return existed

    def list_ids(self) -> list[str]:
        if self._redis is not None:
            keys = self._redis.keys(f"{self.SESSION_PREFIX}*")
            return [k.replace(self.SESSION_PREFIX, "") for k in keys]
        return [
            k.replace(self.SESSION_PREFIX, "")
            for k in self._memory.keys(self.SESSION_PREFIX)
        ]


session_store = SessionStore()
