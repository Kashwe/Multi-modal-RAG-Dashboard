import os
from typing import List, Any
from pydantic import AnyHttpUrl, BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

def parse_cors_origins(v: str | List[str]) -> List[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Multi-Modal RAG Dashboard"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: Annotated[
        Any, BeforeValidator(parse_cors_origins)
    ] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    # File Upload constraints
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB default
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg"]
    UPLOAD_DIR: str = "data/uploads"

    # API Keys & Third Party Config
    GROQ_API_KEY: str = "mock_key_for_development"
    GROQ_MODEL: str = "llama3-8b-8192"

    # Database Config placeholders
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Environment Stage
    ENV: str = "development"

settings = Settings()
