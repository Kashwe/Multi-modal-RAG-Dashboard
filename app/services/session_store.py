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

#     Stores per-session metadata: created_at, last_seen, doc_ids, message_count,
#     plus analytics counters (token usage, latency samples, retrieval scores).
#     """

#     SESSION_PREFIX = "session:"

#     def __init__(self) -> None:
#         self._memory = _InMemoryStore()
#         self._redis = None
#         self._connect_redis()

#     def _connect_redis(self) -> None:
#         try:
#             import redis  # type: ignore

#             client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
#             client.ping()
#             self._redis = client
#             logger.info("Session store connected to Redis at %s", settings.REDIS_URL)
#         except Exception as exc:
#             self._redis = None
#             logger.warning(
#                 "Redis unavailable (%s); using in-memory session store", exc
#             )

#     @property
#     def backend(self) -> str:
#         return "redis" if self._redis is not None else "memory"

#     def _key(self, session_id: str) -> str:
#         return f"{self.SESSION_PREFIX}{session_id}"

#     def create(self) -> str:
#         session_id = uuid.uuid4().hex
#         now = time.time()
#         payload = {
#             "session_id": session_id,
#             "created_at": now,
#             "last_seen": now,
#             "doc_ids": [],
#             "message_count": 0,
#             "tokens": {"prompt": 0, "completion": 0, "total": 0},
#             "latencies_ms": [],
#             "retrieval_scores": [],
#         }
#         self._write(session_id, payload)
#         return session_id

#     def get(self, session_id: str) -> Optional[Dict[str, Any]]:
#         if self._redis is not None:
#             raw = self._redis.get(self._key(session_id))
#             if raw is None:
#                 return None
#             return json.loads(raw)
#         return self._memory.get(self._key(session_id))

#     def _write(self, session_id: str, payload: Dict[str, Any]) -> None:
#         payload["last_seen"] = time.time()
#         if self._redis is not None:
#             self._redis.set(
#                 self._key(session_id), json.dumps(payload), ex=settings.SESSION_TTL
#             )
#         else:
#             self._memory.set(self._key(session_id), payload, settings.SESSION_TTL)

#     def update(self, session_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
#         payload = self.get(session_id)
#         if payload is None:
#             return None
#         payload.update(fields)
#         self._write(session_id, payload)
#         return payload

#     def append(self, session_id: str, field: str, value: Any) -> Optional[Dict[str, Any]]:
#         payload = self.get(session_id)
#         if payload is None:
#             return None
#         payload.setdefault(field, []).append(value)
#         self._write(session_id, payload)
#         return payload

#     def add_tokens(
#         self, session_id: str, prompt: int, completion: int
#     ) -> Optional[Dict[str, Any]]:
#         payload = self.get(session_id)
#         if payload is None:
#             return None
#         tokens = payload.setdefault(
#             "tokens", {"prompt": 0, "completion": 0, "total": 0}
#         )
#         tokens["prompt"] += prompt
#         tokens["completion"] += completion
#         tokens["total"] = tokens["prompt"] + tokens["completion"]
#         payload["message_count"] = payload.get("message_count", 0) + 1
#         self._write(session_id, payload)
#         return payload

#     def delete(self, session_id: str) -> bool:
#         key = self._key(session_id)
#         if self._redis is not None:
#             return bool(self._redis.delete(key))
#         existed = self._memory.get(key) is not None
#         self._memory.delete(key)
#         return existed

#     def list_ids(self) -> list[str]:
#         if self._redis is not None:
#             keys = self._redis.keys(f"{self.SESSION_PREFIX}*")
#             return [k.replace(self.SESSION_PREFIX, "") for k in keys]
#         return [
#             k.replace(self.SESSION_PREFIX, "")
#             for k in self._memory.keys(self.SESSION_PREFIX)
#         ]


# session_store = SessionStore()










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

#     Now extended for RBAC:
#     - user_id
#     - role
#     """

#     SESSION_PREFIX = "session:"

#     def __init__(self) -> None:
#         self._memory = _InMemoryStore()
#         self._redis = None
#         self._connect_redis()

#     def _connect_redis(self) -> None:
#         try:
#             import redis  # type: ignore

#             client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
#             client.ping()
#             self._redis = client
#             logger.info("Session store connected to Redis at %s", settings.REDIS_URL)
#         except Exception as exc:
#             self._redis = None
#             logger.warning(
#                 "Redis unavailable (%s); using in-memory session store", exc
#             )

#     @property
#     def backend(self) -> str:
#         return "redis" if self._redis is not None else "memory"

#     def _key(self, session_id: str) -> str:
#         return f"{self.SESSION_PREFIX}{session_id}"

#     # =========================
#     # SESSION CREATION (UPDATED)
#     # =========================
#     def create(self) -> str:
#         session_id = uuid.uuid4().hex
#         now = time.time()

#         payload = {
#             "session_id": session_id,
#             "created_at": now,
#             "last_seen": now,

#             # 🔐 RBAC FIELDS (NEW)
#             "user_id": None,
#             "role": "user",

#             "doc_ids": [],
#             "message_count": 0,
#             "tokens": {"prompt": 0, "completion": 0, "total": 0},
#             "latencies_ms": [],
#             "retrieval_scores": [],
#         }

#         self._write(session_id, payload)
#         return session_id

#     # =========================
#     # CORE GET/WRITE
#     # =========================
#     def get(self, session_id: str) -> Optional[Dict[str, Any]]:
#         if self._redis is not None:
#             raw = self._redis.get(self._key(session_id))
#             if raw is None:
#                 return None
#             return json.loads(raw)
#         return self._memory.get(self._key(session_id))

#     def _write(self, session_id: str, payload: Dict[str, Any]) -> None:
#         payload["last_seen"] = time.time()

#         if self._redis is not None:
#             self._redis.set(
#                 self._key(session_id),
#                 json.dumps(payload),
#                 ex=settings.SESSION_TTL
#             )
#         else:
#             self._memory.set(
#                 self._key(session_id),
#                 payload,
#                 settings.SESSION_TTL
#             )

#     # =========================
#     # UPDATE HELPERS
#     # =========================
#     def update(self, session_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
#         payload = self.get(session_id)
#         if payload is None:
#             return None
#         payload.update(fields)
#         self._write(session_id, payload)
#         return payload

#     def append(self, session_id: str, field: str, value: Any) -> Optional[Dict[str, Any]]:
#         payload = self.get(session_id)
#         if payload is None:
#             return None
#         payload.setdefault(field, []).append(value)
#         self._write(session_id, payload)
#         return payload

#     def add_tokens(self, session_id: str, prompt: int, completion: int) -> Optional[Dict[str, Any]]:
#         payload = self.get(session_id)
#         if payload is None:
#             return None

#         tokens = payload.setdefault(
#             "tokens",
#             {"prompt": 0, "completion": 0, "total": 0}
#         )

#         tokens["prompt"] += prompt
#         tokens["completion"] += completion
#         tokens["total"] = tokens["prompt"] + tokens["completion"]

#         payload["message_count"] = payload.get("message_count", 0) + 1

#         self._write(session_id, payload)
#         return payload

#     # =========================
#     # RBAC HELPERS (NEW)
#     # =========================
#     def attach_user(self, session_id: str, user_id: str, role: str = "user"):
#         """
#         Call this after login/authentication
#         """
#         return self.update(
#             session_id,
#             user_id=user_id,
#             role=role
#         )

#     def get_user(self, session_id: str) -> Optional[Dict[str, Any]]:
#         session = self.get(session_id)
#         if not session:
#             return None

#         return {
#             "id": session.get("user_id"),
#             "role": session.get("role", "user")
#         }

#     # =========================
#     # DELETE + LIST
#     # =========================
#     def delete(self, session_id: str) -> bool:
#         key = self._key(session_id)

#         if self._redis is not None:
#             return bool(self._redis.delete(key))

#         existed = self._memory.get(key) is not None
#         self._memory.delete(key)
#         return existed

#     def list_ids(self) -> list[str]:
#         if self._redis is not None:
#             keys = self._redis.keys(f"{self.SESSION_PREFIX}*")
#             return [k.replace(self.SESSION_PREFIX, "") for k in keys]

#         return [
#             k.replace(self.SESSION_PREFIX, "")
#             for k in self._memory.keys(self.SESSION_PREFIX)
#         ]


# session_store = SessionStore()





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
#     SESSION_PREFIX = "session:"

#     def __init__(self) -> None:
#         self._memory = _InMemoryStore()
#         self._redis = None
#         self._connect_redis()

#     def _connect_redis(self) -> None:
#         try:
#             import redis  # type: ignore

#             client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
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
#             "tokens": {"prompt": 0, "completion": 0, "total": 0},
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
#             self._memory.set(self._key(session_id), payload, settings.SESSION_TTL)

#     def update(self, session_id: str, **fields: Any):
#         session = self.get(session_id)
#         if not session:
#             return None
#         session.update(fields)
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
#         return [k.replace(self.SESSION_PREFIX, "") for k in self._memory.keys(self.SESSION_PREFIX)]


# session_store = SessionStore()






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

#     # ✅ FIX 1: backend property (THIS WAS MISSING)
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

#     def delete(self, session_id: str) -> bool:
#         key = self._key(session_id)

#         if self._redis:
#             return bool(self._redis.delete(key))

#         existed = self._memory.get(key) is not None
#         self._memory.delete(key)
#         return existed

#     def append(self, session_id: str, field: str, value: Any):
#     session = self.get(session_id)
#     if not session:
#         return None

#     session.setdefault(field, []).append(value)
#     self._write(session_id, session)
#     return session

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
    Stores:
    - identity (user_id, role)
    - document ownership tracking
    - analytics metrics
    """

    SESSION_PREFIX = "session:"

    def __init__(self) -> None:
        self._memory = _InMemoryStore()
        self._redis = None
        self._connect_redis()

    # ✅ FIX: backend property
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
            return [k.replace(self.SESSION_PREFIX, "") for k in keys]

        return [
            k.replace(self.SESSION_PREFIX, "")
            for k in self._memory.keys(self.SESSION_PREFIX)
        ]


session_store = SessionStore()