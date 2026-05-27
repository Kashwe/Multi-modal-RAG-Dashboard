from fastapi import APIRouter

from app.api.v1.endpoints import analytics, documents, query, sessions

api_router = APIRouter()
api_router.include_router(sessions.router)
api_router.include_router(documents.router)
api_router.include_router(query.router)
api_router.include_router(analytics.router)
