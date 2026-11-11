import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user, record_audit_log, require_contractor
from app.core.constants import AuditAction, MediaType
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
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
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

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="SiteSurvey",
        resource_id=survey.id,
        change_details={"site_id": survey.site_id, "survey_date": str(survey.survey_date)},
        request=request,
    )

    resp = SurveyResponse.model_validate(survey)
    resp.images = []
    return resp


@router.get("/", response_model=List[SurveyResponse])
async def list_surveys(
    site_id: Optional[str] = Query(None, description="Filter surveys by demolition site ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List site surveys, optionally filtered by site."""
    query = select(SiteSurvey)
    if site_id:
        query = query.filter(SiteSurvey.site_id == site_id)
    query = query.order_by(SiteSurvey.survey_date.desc(), SiteSurvey.created_at.desc())

    result = await db.execute(query)
    surveys = list(result.scalars().all())
    output = []
    for s in surveys:
        s_resp = SurveyResponse.model_validate(s)
        s_resp.images = [SurveyImageResponse.model_validate(img) for img in (s.images or [])]
        output.append(s_resp)
    return output


@router.get("/{survey_id}", response_model=SurveyResponse)
async def get_survey(
    survey_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve survey inspection details along with media records."""
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
    current_user: User = Depends(require_contractor),
):
    """Generate S3 presigned URL for direct, secure multi-megabyte image/video upload."""
    survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
    if not survey_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    file_ext = req.file_name.split(".")[-1] if "." in req.file_name else "jpg"
    folder = "raw_videos" if req.media_type == MediaType.VIDEO else "raw_surveys"
    unique_key = f"{folder}/{survey_id}/{uuid.uuid4()}.{file_ext}"

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
    request: Request,
    file: UploadFile = File(...),
    media_type: str = Form("IMAGE"),
    camera_altitude_m: Optional[float] = Form(None),
    focal_length_mm: Optional[float] = Form(None),
    sensor_width_mm: Optional[float] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Upload survey photo or drone video directly to backend."""
    survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
    survey = survey_res.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    file_bytes = await file.read()
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"

    is_video = media_type.upper() == "VIDEO" or (file.content_type and "video" in file.content_type)
    media_type_enum = MediaType.VIDEO if is_video else MediaType.IMAGE
    folder = "raw_videos" if is_video else "raw_surveys"
    unique_key = f"{folder}/{survey_id}/{uuid.uuid4()}.{file_ext}"

    # Ensure bucket exists
    storage_service.ensure_bucket_exists()
    storage_service.upload_bytes(file_bytes, unique_key, content_type=file.content_type or ("video/mp4" if is_video else "image/jpeg"))

    # Compute GSD if parameters provided
    gsd_val = None
    if camera_altitude_m and focal_length_mm and sensor_width_mm and focal_length_mm > 0:
        # GSD formula: (Altitude_m * Sensor_width_mm * 100) / (Focal_length_mm * image_width_px)
        # Assuming typical 4000px sensor if width not yet decoded
        gsd_val = (camera_altitude_m * sensor_width_mm * 100.0) / (focal_length_mm * 4000.0)

    image_record = SurveyImage(
        survey_id=survey_id,
        file_name=file.filename,
        media_type=media_type_enum,
        original_s3_key=unique_key,
        file_size_bytes=len(file_bytes),
        mime_type=file.content_type or ("video/mp4" if is_video else "image/jpeg"),
        camera_altitude_m=camera_altitude_m,
        focal_length_mm=focal_length_mm,
        sensor_width_mm=sensor_width_mm,
        gsd_cm_per_px=gsd_val,
    )
    db.add(image_record)

    survey.total_images_count += 1
    await db.commit()
    await db.refresh(image_record)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.UPLOAD,
        resource_type="SurveyImage",
        resource_id=image_record.id,
        change_details={"file_name": file.filename, "media_type": media_type_enum.value, "size_bytes": len(file_bytes)},
        request=request,
    )

    down_url = storage_service.generate_presigned_download_url(unique_key)
    resp = SurveyImageResponse.model_validate(image_record)
    resp.download_url = down_url
    return resp
