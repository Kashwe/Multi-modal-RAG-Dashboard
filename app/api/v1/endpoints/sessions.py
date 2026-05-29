# from fastapi import APIRouter, HTTPException, status

# from app.schemas.session import (
#     SessionCreateResponse,
#     SessionInfo,
#     SessionListResponse,
#     TokenUsage,
# )
# from app.services.session_store import session_store

# router = APIRouter(prefix="/sessions", tags=["Sessions"])


# @router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
# async def create_session() -> SessionCreateResponse:
#     session_id = session_store.create()
#     return SessionCreateResponse(session_id=session_id, backend=session_store.backend)


# @router.get("", response_model=SessionListResponse)
# async def list_sessions() -> SessionListResponse:
#     ids = session_store.list_ids()
#     return SessionListResponse(
#         backend=session_store.backend, count=len(ids), session_ids=ids
#     )


# @router.get("/{session_id}", response_model=SessionInfo)
# async def get_session(session_id: str) -> SessionInfo:
#     payload = session_store.get(session_id)
#     if payload is None:
#         raise HTTPException(status_code=404, detail="session not found")
#     return SessionInfo(
#         session_id=payload["session_id"],
#         created_at=payload["created_at"],
#         last_seen=payload["last_seen"],
#         doc_ids=payload.get("doc_ids", []),
#         message_count=payload.get("message_count", 0),
#         tokens=TokenUsage(**payload.get("tokens", {})),
#     )


# @router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_session(session_id: str) -> None:
#     if not session_store.delete(session_id):
#         raise HTTPException(status_code=404, detail="session not found")








# from fastapi import APIRouter, HTTPException, status

# from app.schemas.session import (
#     SessionCreateResponse,
#     SessionInfo,
#     SessionListResponse,
#     TokenUsage,
# )
# from app.services.session_store import session_store

# # 🔐 RBAC
# from app.core.rbac import require_role

# router = APIRouter(prefix="/sessions", tags=["Sessions"])


# @router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
# async def create_session() -> SessionCreateResponse:
#     session_id = session_store.create()
#     return SessionCreateResponse(session_id=session_id, backend=session_store.backend)


# @router.get("", response_model=SessionListResponse)
# async def list_sessions() -> SessionListResponse:

#     # 🔐 OPTIONAL PROTECTION
#     # require_role(session, "admin")

#     ids = session_store.list_ids()
#     return SessionListResponse(
#         backend=session_store.backend,
#         count=len(ids),
#         session_ids=ids
#     )


# @router.get("/{session_id}", response_model=SessionInfo)
# async def get_session(session_id: str) -> SessionInfo:

#     session = session_store.get(session_id)

#     if session is None:
#         raise HTTPException(status_code=404, detail="session not found")

#     return SessionInfo(
#         session_id=session["session_id"],
#         created_at=session["created_at"],
#         last_seen=session["last_seen"],
#         doc_ids=session.get("doc_ids", []),
#         message_count=session.get("message_count", 0),
#         tokens=TokenUsage(**session.get("tokens", {})),
#     )


# @router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_session(session_id: str) -> None:

#     if not session_store.delete(session_id):
#         raise HTTPException(status_code=404, detail="session not found")





from fastapi import APIRouter, HTTPException, status

from app.schemas.session import (
    SessionCreateResponse,
    SessionInfo,
    SessionListResponse,
    TokenUsage,
)
from app.services.session_store import session_store
from app.core.rbac import require_role

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session() -> SessionCreateResponse:
    session_id = session_store.create(user_id="user_1", role="user")
    return SessionCreateResponse(session_id=session_id, backend=session_store.backend)


@router.get("", response_model=SessionListResponse)
async def list_sessions(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(404, "session not found")

    require_role(session, "admin")

    ids = session_store.list_ids()
    return SessionListResponse(
        backend=session_store.backend,
        count=len(ids),
        session_ids=ids
    )


@router.get("/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(404, "session not found")

    return SessionInfo(
        session_id=session["session_id"],
        created_at=session["created_at"],
        last_seen=session["last_seen"],
        doc_ids=session.get("doc_ids", []),
        message_count=session.get("message_count", 0),
        tokens=TokenUsage(**session.get("tokens", {})),
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    if not session_store.delete(session_id):
        raise HTTPException(404, "session not found")