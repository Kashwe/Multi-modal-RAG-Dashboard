# import json
# import logging
# import threading
# import time
# import uuid
# from typing import Any, Dict, Optional

# from app.core.config import settings

# logger = logging.getLogger(__name__)


# class _InMemoryStore:
#     def __init__(self) -> None:
#         self._data: Dict[str, Dict[str, Any]] = {}
#         self._expiry: Dict[str, float] = {}
#         self._lock = threading.RLock()

#     def _purge(self, key: str) -> None:
#         if key in self._expiry and self._expiry[key] < time.time():
#             self._data.pop(key, None)
#             self._expiry.pop(key, None)

#     def get(self, key: str) -> Optional[Dict[str, Any]]:
#         with self._lock:
#             self._purge(key)
#             return self._data.get(key)

#     def set(self, key: str, value: Dict[str, Any], ttl: int) -> None:
#         with self._lock:
#             self._data[key] = value
#             self._expiry[key] = time.time() + ttl

#     def delete(self, key: str) -> None:
#         with self._lock:
#             self._data.pop(key, None)
#             self._expiry.pop(key, None)

#     def keys(self, prefix: str) -> list[str]:
#         with self._lock:
#             return [k for k in list(self._data.keys()) if k.startswith(prefix)]


# class SessionStore:
#     """
#     Session store with Redis backend and in-memory fallback.
#     Stores:
#     - identity (user_id, role)
#     - document ownership tracking
#     - analytics metrics
#     """

#     SESSION_PREFIX = "session:"

#     def __init__(self) -> None:
#         self._memory = _InMemoryStore()
#         self._redis = None
#         self._connect_redis()

#     # ✅ FIX: backend property
#     @property
#     def backend(self) -> str:
#         return "redis" if self._redis is not None else "memory"

#     def _connect_redis(self) -> None:
#         try:
#             import redis  # type: ignore

#             client = redis.Redis.from_url(
#                 settings.REDIS_URL,
#                 decode_responses=True
#             )
#             client.ping()
#             self._redis = client
#             logger.info("Session store connected to Redis")
#         except Exception as exc:
#             self._redis = None
#             logger.warning("Redis unavailable: %s", exc)

#     def _key(self, session_id: str) -> str:
#         return f"{self.SESSION_PREFIX}{session_id}"

#     def create(self, user_id: str = "anonymous", role: str = "user") -> str:
#         session_id = uuid.uuid4().hex
#         now = time.time()

#         payload = {
#             "session_id": session_id,
#             "user_id": user_id,
#             "role": role,
#             "created_at": now,
#             "last_seen": now,
#             "doc_ids": [],
#             "message_count": 0,
#             "tokens": {
#                 "prompt": 0,
#                 "completion": 0,
#                 "total": 0
#             },
#             "latencies_ms": [],
#             "retrieval_scores": [],
#         }

#         self._write(session_id, payload)
#         return session_id

#     def get(self, session_id: str) -> Optional[Dict[str, Any]]:
#         if self._redis:
#             raw = self._redis.get(self._key(session_id))
#             return json.loads(raw) if raw else None
#         return self._memory.get(self._key(session_id))

#     def _write(self, session_id: str, payload: Dict[str, Any]) -> None:
#         payload["last_seen"] = time.time()

#         if self._redis:
#             self._redis.set(
#                 self._key(session_id),
#                 json.dumps(payload),
#                 ex=settings.SESSION_TTL,
#             )
#         else:
#             self._memory.set(
#                 self._key(session_id),
#                 payload,
#                 settings.SESSION_TTL
#             )

#     def update(self, session_id: str, **fields: Any):
#         session = self.get(session_id)
#         if not session:
#             return None

#         session.update(fields)
#         self._write(session_id, session)
#         return session

#     def append(self, session_id: str, field: str, value: Any):
#         session = self.get(session_id)
#         if not session:
#             return None

#         session.setdefault(field, []).append(value)
#         self._write(session_id, session)
#         return session

#     def add_tokens(self, session_id: str, prompt: int, completion: int):
#         session = self.get(session_id)
#         if not session:
#             return None

#         tokens = session.setdefault(
#             "tokens",
#             {"prompt": 0, "completion": 0, "total": 0}
#         )

#         tokens["prompt"] += prompt
#         tokens["completion"] += completion
#         tokens["total"] = tokens["prompt"] + tokens["completion"]

#         session["message_count"] = session.get("message_count", 0) + 1

#         self._write(session_id, session)
#         return session

#     def delete(self, session_id: str) -> bool:
#         key = self._key(session_id)

#         if self._redis:
#             return bool(self._redis.delete(key))

#         existed = self._memory.get(key) is not None
#         self._memory.delete(key)
#         return existed

#     def list_ids(self) -> list[str]:
#         if self._redis:
#             keys = self._redis.keys(f"{self.SESSION_PREFIX}*")
#             return [k.replace(self.SESSION_PREFIX, "") for k in keys]

#         return [
#             k.replace(self.SESSION_PREFIX, "")
#             for k in self._memory.keys(self.SESSION_PREFIX)
#         ]


# session_store = SessionStore()









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

    def get(self, key: str):
        with self._lock:
            self._purge(key)
            return self._data.get(key)

    def set(self, key: str, value, ttl: int) -> None:
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
    Stores:
    - identity (user_id, role)
    - document ownership tracking
    - analytics metrics
    - query cache
    """

    SESSION_PREFIX = "session:"
    CACHE_PREFIX = "cache:"

    def __init__(self) -> None:
        self._memory = _InMemoryStore()
        self._redis = None
        self._connect_redis()

    @property
    def backend(self) -> str:
        return "redis" if self._redis is not None else "memory"

    def _connect_redis(self) -> None:
        try:
            import redis  # type: ignore

            client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )

            client.ping()

            self._redis = client

            logger.info("Session store connected to Redis")

        except Exception as exc:
            self._redis = None
            logger.warning("Redis unavailable: %s", exc)

    def _key(self, session_id: str) -> str:
        return f"{self.SESSION_PREFIX}{session_id}"

    # ✅ CACHE KEY
    def _cache_key(self, session_id: str, question: str) -> str:
        normalized = question.strip().lower()
        return f"{self.CACHE_PREFIX}{session_id}:{normalized}"

    def create(self, user_id: str = "anonymous", role: str = "user") -> str:
        session_id = uuid.uuid4().hex
        now = time.time()

        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "created_at": now,
            "last_seen": now,
            "doc_ids": [],
            "message_count": 0,
            "tokens": {
                "prompt": 0,
                "completion": 0,
                "total": 0
            },
            "latencies_ms": [],
            "retrieval_scores": [],
        }

        self._write(session_id, payload)

        return session_id

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self._redis:
            raw = self._redis.get(self._key(session_id))
            return json.loads(raw) if raw else None

        return self._memory.get(self._key(session_id))

    def _write(self, session_id: str, payload: Dict[str, Any]) -> None:
        payload["last_seen"] = time.time()

        if self._redis:
            self._redis.set(
                self._key(session_id),
                json.dumps(payload),
                ex=settings.SESSION_TTL,
            )
        else:
            self._memory.set(
                self._key(session_id),
                payload,
                settings.SESSION_TTL
            )

    def update(self, session_id: str, **fields: Any):
        session = self.get(session_id)

        if not session:
            return None

        session.update(fields)

        self._write(session_id, session)

        return session

    def append(self, session_id: str, field: str, value: Any):
        session = self.get(session_id)

        if not session:
            return None

        session.setdefault(field, []).append(value)

        self._write(session_id, session)

        return session

    def add_tokens(self, session_id: str, prompt: int, completion: int):
        session = self.get(session_id)

        if not session:
            return None

        tokens = session.setdefault(
            "tokens",
            {"prompt": 0, "completion": 0, "total": 0}
        )

        tokens["prompt"] += prompt
        tokens["completion"] += completion
        tokens["total"] = tokens["prompt"] + tokens["completion"]

        session["message_count"] = session.get("message_count", 0) + 1

        self._write(session_id, session)

        return session

    # ✅ GET CACHE
    def get_cache(self, session_id: str, question: str):
        key = self._cache_key(session_id, question)

        if self._redis:
            value = self._redis.get(key)
            return json.loads(value) if value else None

        return self._memory.get(key)

    # ✅ SET CACHE
    def set_cache(self, session_id: str, question: str, value: dict):
        key = self._cache_key(session_id, question)

        if self._redis:
            self._redis.set(
                key,
                json.dumps(value),
                ex=3600
            )
        else:
            self._memory.set(
                key,
                value,
                ttl=3600
            )

    def delete(self, session_id: str) -> bool:
        key = self._key(session_id)

        if self._redis:
            return bool(self._redis.delete(key))

        existed = self._memory.get(key) is not None

        self._memory.delete(key)

        return existed

    def list_ids(self) -> list[str]:
        if self._redis:
            keys = self._redis.keys(f"{self.SESSION_PREFIX}*")

            return [
                k.replace(self.SESSION_PREFIX, "")
                for k in keys
            ]

        return [
            k.replace(self.SESSION_PREFIX, "")
            for k in self._memory.keys(self.SESSION_PREFIX)
        ]


session_store = SessionStore()