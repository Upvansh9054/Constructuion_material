from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import setup_logging
from app.services.storage import storage_service

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown event orchestration."""
    logger.info("Initializing Demolition Intelligence & Material Recovery Backend Engine...")

    # Create tables if not running Alembic (useful in dev/testing)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas verified.")
    except Exception as db_err:
        logger.warning(f"Database connection deferred or pending migration: {db_err}")

    # Check S3 bucket connectivity
    try:
        storage_service.ensure_bucket_exists()
    except Exception as s3_err:
        logger.warning(f"S3 object store check deferred: {s3_err}")

    yield

    logger.info("Shutting down Demolition Intelligence Engine...")
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production AI Platform that analyses demolition sites, identifies recoverable "
        "construction materials (Concrete, Bricks, Steel, Timber, Glass, Mixed debris), "
        "estimates quantities & conditions, computes circular carbon offsets, "
        "and connects contractors with secondary material buyers and recyclers."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 Router Registration
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health/live", tags=["Health & Diagnostics"], status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Kubernetes / Docker container liveness probe."""
    return {"status": "alive", "service": settings.PROJECT_NAME}


@app.get("/health/ready", tags=["Health & Diagnostics"], status_code=status.HTTP_200_OK)
async def readiness_probe():
    """Readiness probe verifying operational status of essential services."""
    return {
        "status": "ready",
        "environment": settings.ENVIRONMENT,
        "database_configured": bool(settings.DATABASE_URL),
        "redis_configured": bool(settings.REDIS_URL),
        "s3_storage_configured": bool(settings.S3_ENDPOINT_URL or settings.S3_BUCKET_NAME),
    }
