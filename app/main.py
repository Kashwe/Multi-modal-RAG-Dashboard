import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging

# Setup base loggers
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Scalable FastAPI Backend for Multi-Modal RAG Dashboard, integrated with Groq LLM API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request processing timer and global error-handling middleware
@app.middleware("http")
async def process_time_and_exceptions_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as exc:
        logging.exception(f"Unhandled server error on path {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred. Please contact the administrator.",
                "error_class": exc.__class__.__name__
            }
        )

# Health Check Route
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "project": settings.PROJECT_NAME,
        "groq_configured": settings.GROQ_API_KEY != "mock_key_for_development"
    }

# Versioned API routes registration placeholder
# Will import v1 api_router and mount it when endpoints are declared
# from app.api.v1.api import api_router
# app.include_router(api_router, prefix=settings.API_V1_STR)
