import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, record_audit_log, require_contractor
from app.core.constants import AuditAction, JobStatus, MediaType, UserRole
from app.core.database import get_db
from app.models.analysis_job import AnalysisJob
from app.models.site import DemolitionSite
from app.models.survey import SiteSurvey, SurveyImage
from app.models.user import User
from app.schemas.survey import (
    MediaStatusResponse,
    MediaUploadBatchResponse,
    PresignedUploadUrlRequest,
    PresignedUploadUrlResponse,
    SurveyCreate,
    SurveyImageResponse,
    SurveyResponse,
    SurveyUpdate,
    VideoExtractionRequest,
)
from app.services.media_processor import (
    MAX_IMAGE_SIZE_BYTES,
    MAX_VIDEO_SIZE_BYTES,
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
    media_processor,
)
from app.services.storage import storage_service

router = APIRouter()


def _build_image_response(img: SurveyImage) -> SurveyImageResponse:
    down_url = storage_service.generate_presigned_download_url(img.original_s3_key)
    thumb_url = (
        storage_service.generate_presigned_download_url(img.thumbnail_s3_key)
        if img.thumbnail_s3_key
        else down_url
    )
    img_resp = SurveyImageResponse.model_validate(img)
    img_resp.download_url = down_url
    img_resp.thumbnail_url = thumb_url
    return img_resp


@router.post("/", response_model=SurveyResponse, status_code=status.HTTP_201_CREATED)
async def create_survey(
    survey_in: SurveyCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Create a new demolition site survey / assessment session."""
    # Check site exists
    site_result = await db.execute(
        select(DemolitionSite).filter(DemolitionSite.id == survey_in.site_id)
    )
    site = site_result.scalar_one_or_none()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Demolition site not found"
        )

    # Permission check: contractor must own the site or be admin
    if (
        not current_user.is_superuser
        and current_user.role != UserRole.ADMIN
        and site.contractor_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create surveys for this site",
        )

    survey = SiteSurvey(
        **survey_in.model_dump(),
        surveyor_id=current_user.id,
        processing_status="IDLE",
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
        change_details={
            "site_id": survey.site_id,
            "assessment_name": survey.assessment_name,
            "survey_date": str(survey.survey_date),
        },
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
        s_resp.images = [
            _build_image_response(img)
            for img in (s.images or [])
            if not getattr(img, "deleted_at", None)
        ]
        output.append(s_resp)
    return output


@router.get("/media-file")
async def get_media_file(
    key: str = Query(..., description="S3 storage key"),
):
    """Stream media file bytes directly (useful for local development, previews, and testing)."""
    try:
        data = storage_service.download_bytes(key)
        ext = key.split(".")[-1].lower() if "." in key else "jpg"
        content_type = "video/mp4" if ext in ("mp4", "mov", "avi", "webm") else f"image/{ext}"
        if ext == "jpg":
            content_type = "image/jpeg"
        return Response(content=data, media_type=content_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Media file not found: {e}"
        )


@router.get("/{survey_id}", response_model=SurveyResponse)
async def get_survey(
    survey_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve survey inspection details along with active media records."""
    result = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    # Fetch active (non-deleted) images
    images_result = await db.execute(
        select(SurveyImage)
        .filter(SurveyImage.survey_id == survey_id, SurveyImage.deleted_at.is_(None))
        .order_by(SurveyImage.created_at.asc())
    )
    images = list(images_result.scalars().all())

    resp = SurveyResponse.model_validate(survey)
    resp.images = [_build_image_response(img) for img in images]
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
    """Single direct file upload with photogrammetry calibration."""
    survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
    survey = survey_res.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    file_bytes = await file.read()
    ext = Path(file.filename or "").suffix.lower()

    is_video = (
        media_type.upper() == "VIDEO"
        or ext in SUPPORTED_VIDEO_EXTENSIONS
        or (file.content_type and "video" in file.content_type)
    )
    media_type_enum = MediaType.VIDEO if is_video else MediaType.IMAGE
    folder = "raw_videos" if is_video else "raw_surveys"
    unique_key = f"{folder}/{survey_id}/{uuid.uuid4()}{ext}"

    storage_service.ensure_bucket_exists()
    storage_service.upload_bytes(
        file_bytes,
        unique_key,
        content_type=file.content_type or ("video/mp4" if is_video else "image/jpeg"),
    )

    # Photogrammetric GSD estimate
    gsd_val = None
    if camera_altitude_m and focal_length_mm and sensor_width_mm and focal_length_mm > 0:
        gsd_val = (camera_altitude_m * sensor_width_mm * 100.0) / (focal_length_mm * 4000.0)

    image_record = SurveyImage(
        survey_id=survey_id,
        file_name=file.filename or "uploaded_media",
        media_type=media_type_enum,
        original_s3_key=unique_key,
        file_size_bytes=len(file_bytes),
        mime_type=file.content_type or ("video/mp4" if is_video else "image/jpeg"),
        camera_altitude_m=camera_altitude_m,
        focal_length_mm=focal_length_mm,
        sensor_width_mm=sensor_width_mm,
        gsd_cm_per_px=gsd_val,
        processing_status="PENDING",
    )
    db.add(image_record)
    await db.commit()
    await db.refresh(image_record)

    # Process derivatives
    if not is_video:
        await media_processor.process_survey_image(db, image_record, file_bytes)
        survey.total_images_count += 1
    else:
        await media_processor.process_survey_video(db, image_record, file_bytes)
        survey.total_images_count += 1

    survey.processing_status = "MEDIA_READY"
    await db.commit()
    await db.refresh(image_record)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.UPLOAD,
        resource_type="SurveyImage",
        resource_id=image_record.id,
        change_details={
            "file_name": file.filename,
            "media_type": media_type_enum.value,
            "size_bytes": len(file_bytes),
        },
        request=request,
    )

    return _build_image_response(image_record)


@router.post("/{survey_id}/upload-media", response_model=MediaUploadBatchResponse)
async def upload_multiple_media(
    survey_id: str,
    request: Request,
    files: List[UploadFile] = File(...),
    camera_altitude_m: Optional[float] = Form(None),
    focal_length_mm: Optional[float] = Form(None),
    sensor_width_mm: Optional[float] = Form(None),
    interval_seconds: float = Form(1.0),
    similarity_threshold: float = Form(0.97),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """
    Enterprise batch upload endpoint:
    - Accepts multiple photographs and videos
    - Validates extensions, size limits, and corruption
    - Generates thumbnails, normalized CV copies, and metadata
    - Extracts non-duplicate video frames at configurable interval
    - Creates and updates analysis job progress
    """
    survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
    survey = survey_res.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    site_res = await db.execute(select(DemolitionSite).filter(DemolitionSite.id == survey.site_id))
    site = site_res.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    if (
        not current_user.is_superuser
        and current_user.role != UserRole.ADMIN
        and site.contractor_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: You do not own this demolition site project",
        )

    # Initialize / link an analysis job to track processing
    job = AnalysisJob(
        id=str(uuid.uuid4()),
        survey_id=survey.id,
        status=JobStatus.IN_PROGRESS,
        progress_percentage=10,
        total_images_count=len(files),
    )
    db.add(job)
    survey.processing_status = "PROCESSING_MEDIA"
    await db.commit()

    processed_responses: List[SurveyImageResponse] = []
    error_messages: List[str] = []
    uploaded_count = 0
    failed_count = 0

    storage_service.ensure_bucket_exists()

    gsd_val = None
    if camera_altitude_m and focal_length_mm and sensor_width_mm and focal_length_mm > 0:
        gsd_val = (camera_altitude_m * sensor_width_mm * 100.0) / (focal_length_mm * 4000.0)

    for idx, f in enumerate(files):
        try:
            file_bytes = await f.read()
            ext = Path(f.filename or "").suffix.lower()

            if ext in SUPPORTED_IMAGE_EXTENSIONS:
                # 1. Image validation & size check
                if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
                    err = f"File '{f.filename}' exceeds 50MB image limit."
                    error_messages.append(err)
                    failed_count += 1
                    continue

                unique_key = f"raw_surveys/{survey_id}/{uuid.uuid4()}{ext}"
                storage_service.upload_bytes(
                    file_bytes, unique_key, content_type=f.content_type or "image/jpeg"
                )

                img_record = SurveyImage(
                    survey_id=survey_id,
                    file_name=f.filename or f"survey_image_{idx}.jpg",
                    media_type=MediaType.IMAGE,
                    original_s3_key=unique_key,
                    file_size_bytes=len(file_bytes),
                    mime_type=f.content_type or "image/jpeg",
                    camera_altitude_m=camera_altitude_m,
                    focal_length_mm=focal_length_mm,
                    sensor_width_mm=sensor_width_mm,
                    gsd_cm_per_px=gsd_val,
                    processing_status="PENDING",
                )
                db.add(img_record)
                await db.commit()
                await db.refresh(img_record)

                # Process thumbnail, CV copy, EXIF
                await media_processor.process_survey_image(db, img_record, file_bytes)

                survey.total_images_count += 1
                uploaded_count += 1
                processed_responses.append(_build_image_response(img_record))

            elif ext in SUPPORTED_VIDEO_EXTENSIONS:
                # 2. Video validation & size check
                if len(file_bytes) > MAX_VIDEO_SIZE_BYTES:
                    err = f"File '{f.filename}' exceeds 500MB video limit."
                    error_messages.append(err)
                    failed_count += 1
                    continue

                unique_key = f"raw_videos/{survey_id}/{uuid.uuid4()}{ext}"
                storage_service.upload_bytes(
                    file_bytes, unique_key, content_type=f.content_type or "video/mp4"
                )

                video_record = SurveyImage(
                    survey_id=survey_id,
                    file_name=f.filename or f"survey_video_{idx}.mp4",
                    media_type=MediaType.VIDEO,
                    original_s3_key=unique_key,
                    file_size_bytes=len(file_bytes),
                    mime_type=f.content_type or "video/mp4",
                    camera_altitude_m=camera_altitude_m,
                    focal_length_mm=focal_length_mm,
                    sensor_width_mm=sensor_width_mm,
                    gsd_cm_per_px=gsd_val,
                    processing_status="PENDING",
                )
                db.add(video_record)
                await db.commit()
                await db.refresh(video_record)

                # Extract deduplicated frames
                extracted_frames = await media_processor.process_survey_video(
                    session=db,
                    video_record=video_record,
                    video_bytes=file_bytes,
                    interval_seconds=interval_seconds,
                    similarity_threshold=similarity_threshold,
                )

                survey.total_images_count += 1
                uploaded_count += 1
                processed_responses.append(_build_image_response(video_record))
                for frame_rec in extracted_frames:
                    processed_responses.append(_build_image_response(frame_rec))

            else:
                err = f"File '{f.filename}' has unsupported extension '{ext}'. Supported: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS))}"
                error_messages.append(err)
                failed_count += 1

            # Update job progress
            pct = int(((idx + 1) / len(files)) * 90) + 10
            job.progress_percentage = min(100, pct)
            await db.commit()

        except Exception as e:
            failed_count += 1
            error_messages.append(f"Error processing file '{f.filename}': {str(e)}")

    # Finalize survey status & job
    survey.processing_status = "MEDIA_READY"
    job.status = JobStatus.SUCCESS if failed_count == 0 else JobStatus.QUEUED
    job.progress_percentage = 100
    job.completed_at = datetime.now(timezone.utc)
    await db.commit()

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.UPLOAD,
        resource_type="SiteSurvey",
        resource_id=survey.id,
        change_details={
            "uploaded_count": uploaded_count,
            "failed_count": failed_count,
            "errors": error_messages,
        },
        request=request,
    )

    return MediaUploadBatchResponse(
        survey_id=survey_id,
        job_id=job.id,
        uploaded_count=uploaded_count,
        failed_count=failed_count,
        images=processed_responses,
        errors=error_messages,
    )


@router.post("/{survey_id}/extract-video-frames", response_model=List[SurveyImageResponse])
async def extract_video_frames_endpoint(
    survey_id: str,
    req: VideoExtractionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Trigger on-demand frame extraction with configurable interval and similarity deduplication."""
    survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
    survey = survey_res.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    video_res = await db.execute(
        select(SurveyImage).filter(
            SurveyImage.id == req.video_id,
            SurveyImage.survey_id == survey_id,
            SurveyImage.media_type == MediaType.VIDEO,
            SurveyImage.deleted_at.is_(None),
        )
    )
    video = video_res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video record not found")

    # Download raw video bytes
    video_bytes = storage_service.download_bytes(video.original_s3_key)

    extracted_frames = await media_processor.process_survey_video(
        session=db,
        video_record=video,
        video_bytes=video_bytes,
        interval_seconds=req.interval_seconds,
        similarity_threshold=req.similarity_threshold,
    )

    return [_build_image_response(fr) for fr in extracted_frames]


@router.get("/{survey_id}/media", response_model=List[SurveyImageResponse])
async def list_survey_media(
    survey_id: str,
    media_type: Optional[MediaType] = Query(None, description="Filter by IMAGE or VIDEO"),
    include_frames: bool = Query(True, description="Include extracted video frames"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active media items for a demolition site survey."""
    query = select(SurveyImage).filter(
        SurveyImage.survey_id == survey_id,
        SurveyImage.deleted_at.is_(None),
    )

    if media_type:
        query = query.filter(SurveyImage.media_type == media_type)

    if not include_frames:
        query = query.filter(SurveyImage.is_extracted_frame.is_(False))

    query = query.order_by(SurveyImage.is_extracted_frame.asc(), SurveyImage.created_at.asc())

    result = await db.execute(query)
    images = list(result.scalars().all())
    return [_build_image_response(img) for img in images]


@router.get("/{survey_id}/media-status", response_model=MediaStatusResponse)
async def get_media_processing_status(
    survey_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll processing status, image counts, and active background job progress."""
    survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
    survey = survey_res.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    # Fetch latest analysis job for this survey
    job_res = await db.execute(
        select(AnalysisJob)
        .filter(AnalysisJob.survey_id == survey_id)
        .order_by(AnalysisJob.created_at.desc())
    )
    job = job_res.scalars().first()

    progress = job.progress_percentage if job else (100 if survey.processing_status == "MEDIA_READY" else 0)

    return MediaStatusResponse(
        survey_id=survey.id,
        processing_status=survey.processing_status,
        total_images_count=survey.total_images_count,
        processed_images_count=survey.processed_images_count,
        extracted_frames_count=survey.extracted_frames_count,
        active_job_id=job.id if job else None,
        progress_percentage=progress,
        error_message=job.error_message if job else None,
    )


@router.delete("/{survey_id}/media/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_survey_media(
    survey_id: str,
    image_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """
    Review and delete media item according to permissions:
    - Soft deletes the media record (and any child extracted video frames)
    - Deletes stored objects from storage
    - Updates survey image counters
    - Demolition Contractor who owns the site or Admin only
    """
    survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
    survey = survey_res.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    site_res = await db.execute(select(DemolitionSite).filter(DemolitionSite.id == survey.site_id))
    site = site_res.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demolition site not found")

    if (
        not current_user.is_superuser
        and current_user.role != UserRole.ADMIN
        and site.contractor_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: You do not own this demolition site project",
        )

    img_res = await db.execute(
        select(SurveyImage).filter(
            SurveyImage.id == image_id,
            SurveyImage.survey_id == survey_id,
            SurveyImage.deleted_at.is_(None),
        )
    )
    img = img_res.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media item not found")

    now = datetime.now(timezone.utc)
    img.deleted_at = now

    # Remove storage files
    if img.original_s3_key:
        storage_service.delete_object(img.original_s3_key)
    if img.thumbnail_s3_key:
        storage_service.delete_object(img.thumbnail_s3_key)
    if img.cv_preprocessed_s3_key:
        storage_service.delete_object(img.cv_preprocessed_s3_key)

    # If it's a video, also delete its extracted child frames
    if img.media_type == MediaType.VIDEO:
        frames_res = await db.execute(
            select(SurveyImage).filter(
                SurveyImage.parent_video_id == img.id,
                SurveyImage.deleted_at.is_(None),
            )
        )
        child_frames = list(frames_res.scalars().all())
        for cf in child_frames:
            cf.deleted_at = now
            if cf.original_s3_key:
                storage_service.delete_object(cf.original_s3_key)
            if cf.thumbnail_s3_key:
                storage_service.delete_object(cf.thumbnail_s3_key)
            if cf.cv_preprocessed_s3_key:
                storage_service.delete_object(cf.cv_preprocessed_s3_key)

    # Recalculate survey counts
    count_res = await db.execute(
        select(func.count(SurveyImage.id)).filter(
            SurveyImage.survey_id == survey_id,
            SurveyImage.deleted_at.is_(None),
        )
    )
    survey.total_images_count = count_res.scalar() or 0
    await db.commit()

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.DELETE,
        resource_type="SurveyImage",
        resource_id=image_id,
        change_details={"file_name": img.file_name, "media_type": img.media_type.value},
        request=request,
    )

    return None
