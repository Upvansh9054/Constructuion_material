import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user
from app.core.constants import JobStatus, SurveyStatus
from app.core.database import get_db
from app.models.analysis_job import AnalysisJob
from app.models.audit_report import DemolitionAuditReport
from app.models.survey import SiteSurvey
from app.models.user import User
from app.schemas.analysis import (
    AnalysisJobResponse,
    AnalysisJobTriggerRequest,
    DemolitionAuditReportResponse,
)
from app.workers.tasks import process_survey_analysis_task

router = APIRouter()


@router.post("/trigger", response_model=AnalysisJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_survey_analysis(
    req: AnalysisJobTriggerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Triggers asynchronous AI analysis pipeline:
    - Object detection (YOLOv8/v11)
    - Volumetric & physical estimation
    - Condition assessment & contamination check
    - Valuation & carbon offset computation
    - Generative AI audit report synthesis (OpenAI API)
    """
    survey_result = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == req.survey_id))
    survey = survey_result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    job = AnalysisJob(
        id=str(uuid.uuid4()),
        survey_id=survey.id,
        status=JobStatus.QUEUED,
        progress_percentage=0,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch to Celery background worker
    try:
        celery_task = process_survey_analysis_task.delay(
            survey_id=survey.id,
            job_id=job.id,
        )
        job.celery_task_id = celery_task.id
        await db.commit()
    except Exception as e:
        # If celery is not running in local test environment, log clear message
        job.status = JobStatus.FAILED
        job.error_message = (
            f"Failed to queue background worker task: {e}. "
            "Please ensure Redis and Celery worker are running."
        )
        await db.commit()

    await db.refresh(job)
    return job


@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
async def get_analysis_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll progress status of an active computer vision analysis job."""
    result = await db.execute(select(AnalysisJob).filter(AnalysisJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis job not found")
    return job


@router.get("/reports/{survey_id}", response_model=DemolitionAuditReportResponse)
async def get_survey_audit_report(
    survey_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve synthesized Demolition Material Audit Report (DMAR)."""
    result = await db.execute(
        select(DemolitionAuditReport).filter(DemolitionAuditReport.survey_id == survey_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demolition audit report not found for this survey. Trigger analysis first.",
        )
    return report
