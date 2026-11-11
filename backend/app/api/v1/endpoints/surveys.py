import uuid
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.site import DemolitionSite
from app.models.survey import SiteSurvey, SurveyImage
from app.models.user import User
from app.schemas.survey import (
    PresignedUploadUrlRequest,
    PresignedUploadUrlResponse,
    SurveyCreate,
    SurveyImageResponse,
    SurveyResponse,
    SurveyUpdate,
)
from app.services.storage import storage_service

router = APIRouter()


@router.post("/", response_model=SurveyResponse, status_code=status.HTTP_201_CREATED)
async def create_survey(
    survey_in: SurveyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new survey inspection session for a site."""
    # Check site exists
    site_result = await db.execute(select(DemolitionSite).filter(DemolitionSite.id == survey_in.site_id))
    if not site_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demolition site not found")

    survey = SiteSurvey(
        **survey_in.model_dump(),
        surveyor_id=current_user.id,
    )
    db.add(survey)
    await db.commit()
    await db.refresh(survey)
    return survey


@router.get("/{survey_id}", response_model=SurveyResponse)
async def get_survey(
    survey_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve survey inspection details along with image records."""
    result = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    # Fetch images
    images_result = await db.execute(select(SurveyImage).filter(SurveyImage.survey_id == survey_id))
    images = list(images_result.scalars().all())

    # Attach presigned download URLs
    image_responses = []
    for img in images:
        down_url = storage_service.generate_presigned_download_url(img.original_s3_key)
        img_resp = SurveyImageResponse.model_validate(img)
        img_resp.download_url = down_url
        image_responses.append(img_resp)

    resp = SurveyResponse.model_validate(survey)
    resp.images = image_responses
    return resp


@router.post("/{survey_id}/presigned-url", response_model=PresignedUploadUrlResponse)
async def get_presigned_upload_url(
    survey_id: str,
    req: PresignedUploadUrlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate S3 presigned URL for direct, secure multi-megabyte image upload."""
    survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
    if not survey_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    file_ext = req.file_name.split(".")[-1] if "." in req.file_name else "jpg"
    unique_key = f"raw_surveys/{survey_id}/{uuid.uuid4()}.{file_ext}"

    url_info = storage_service.generate_presigned_upload_url(
        s3_key=unique_key,
        content_type=req.mime_type,
    )

    return PresignedUploadUrlResponse(
        upload_url=url_info["upload_url"],
        s3_key=unique_key,
    )


@router.post("/{survey_id}/upload-direct", response_model=SurveyImageResponse)
async def upload_survey_image_direct(
    survey_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload survey photo directly to backend (helpful in local dev without client S3 direct upload)."""
    survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
    survey = survey_res.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    file_bytes = await file.read()
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_key = f"raw_surveys/{survey_id}/{uuid.uuid4()}.{file_ext}"

    # Ensure bucket exists in local MinIO
    storage_service.ensure_bucket_exists()
    storage_service.upload_bytes(file_bytes, unique_key, content_type=file.content_type or "image/jpeg")

    image_record = SurveyImage(
        survey_id=survey_id,
        file_name=file.filename,
        original_s3_key=unique_key,
        file_size_bytes=len(file_bytes),
        mime_type=file.content_type or "image/jpeg",
    )
    db.add(image_record)

    survey.total_images_count += 1
    await db.commit()
    await db.refresh(image_record)

    down_url = storage_service.generate_presigned_download_url(unique_key)
    resp = SurveyImageResponse.model_validate(image_record)
    resp.download_url = down_url
    return resp

