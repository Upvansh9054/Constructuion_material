from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.constants import JobStatus
from app.models.base import BaseMixin


class AnalysisJob(Base, BaseMixin):
    __tablename__ = "analysis_jobs"

    survey_id = Column(
        String(36),
        ForeignKey("site_surveys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    celery_task_id = Column(String(255), unique=True, nullable=True, index=True)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False, index=True)
    
    progress_percentage = Column(Integer, default=0, nullable=False)
    processed_images_count = Column(Integer, default=0, nullable=False)
    total_images_count = Column(Integer, default=0, nullable=False)

    error_message = Column(Text, nullable=True)
    execution_metrics = Column(JSON, nullable=True)  # latency, inference time per image, detected count

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    survey = relationship("SiteSurvey", back_populates="analysis_jobs")

