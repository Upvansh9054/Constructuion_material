from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.core.constants import JobStatus


class AnalysisJobTriggerRequest(BaseModel):
    survey_id: str
    run_volumetric_estimation: bool = True
    generate_summary_report: bool = True
    confidence_threshold: Optional[float] = Field(default=0.45, ge=0.1, le=1.0)


class AnalysisJobResponse(BaseModel):
    id: str
    survey_id: str
    celery_task_id: Optional[str] = None
    status: JobStatus
    progress_percentage: int
    processed_images_count: int
    total_images_count: int
    error_message: Optional[str] = None
    execution_metrics: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DemolitionAuditReportResponse(BaseModel):
    id: str
    site_id: str
    survey_id: str
    report_title: str
    executive_summary: str
    regulatory_compliance_notes: Optional[str] = None
    buyer_matching_insights: Optional[str] = None
    total_recoverable_tonnes: float
    total_estimated_value_usd: float
    total_carbon_offset_kg_co2e: float
    detailed_breakdown_json: Dict[str, Any]
    pdf_report_s3_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

