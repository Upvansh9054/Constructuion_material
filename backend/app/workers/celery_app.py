from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "demolition_intelligence_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes max per batch analysis
    task_soft_time_limit=1500,
    worker_prefetch_multiplier=1,  # Prevent worker overload with heavy CV tasks
)

