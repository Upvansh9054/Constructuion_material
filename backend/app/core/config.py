import json
import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Demolition Intelligence & Material Recovery"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "demolition-insecure-dev-secret-key-change-in-production-min32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    ALGORITHM: str = "HS256"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "demolition_user"
    POSTGRES_PASSWORD: str = "demolition_secure_password"
    POSTGRES_DB: str = "demolition_intelligence"
    DATABASE_URL: str = (
        "postgresql+asyncpg://demolition_user:demolition_secure_password@localhost:5432/demolition_intelligence"
    )
    DATABASE_SYNC_URL: str = (
        "postgresql://demolition_user:demolition_secure_password@localhost:5432/demolition_intelligence"
    )

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # S3 Object Storage
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin123"
    S3_BUCKET_NAME: str = "demolition-surveys"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # AI Pipeline Models
    YOLO_MODEL_PATH: str = "ai_pipeline/weights/demolition_materials_yolov8.pt"
    CONFIDENCE_THRESHOLD: float = 0.45
    IOU_THRESHOLD: float = 0.50

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def adjust_for_vercel(cls, v: str) -> str:
        if os.getenv("VERCEL") == "1" and "sqlite" in v and "/tmp" not in v:
            return "sqlite+aiosqlite:////tmp/demolition_intelligence.db"
        return v

    @field_validator("DATABASE_SYNC_URL", mode="after")
    @classmethod
    def adjust_sync_for_vercel(cls, v: str) -> str:
        if os.getenv("VERCEL") == "1" and "sqlite" in v and "/tmp" not in v:
            return "sqlite:////tmp/demolition_intelligence.db"
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

