from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.constants import MediaType, SurveyStatus


class SurveyBase(BaseModel):
    site_id: str
    survey_date: date
    assessment_name: Optional[str] = Field(None, max_length=255, description="Assessment or survey campaign title")
    assessment_type: str = Field(default="PRE_DEMOLITION", max_length=100)
    weather_condition: Optional[str] = None
    survey_notes: Optional[str] = None


class SurveyCreate(SurveyBase):
    pass


class SurveyUpdate(BaseModel):
    assessment_name: Optional[str] = None
    assessment_type: Optional[str] = None
    weather_condition: Optional[str] = None
    survey_notes: Optional[str] = None
    status: Optional[SurveyStatus] = None
    processing_status: Optional[str] = None


class SurveyImageResponse(BaseModel):
    id: str
    survey_id: str
    file_name: str
    media_type: MediaType = MediaType.IMAGE
    original_s3_key: str
    annotated_s3_key: Optional[str] = None
    thumbnail_s3_key: Optional[str] = None
    cv_preprocessed_s3_key: Optional[str] = None
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_size_bytes: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None

    # Video attributes & frame extraction hierarchy
    is_extracted_frame: bool = False
    parent_video_id: Optional[str] = None
    frame_index: Optional[int] = None
    timestamp_seconds: Optional[float] = None
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    codec: Optional[str] = None

    # Processing status & photogrammetry calibration
    processing_status: str = "PROCESSED"
    error_message: Optional[str] = None
    camera_altitude_m: Optional[float] = None
    focal_length_mm: Optional[float] = None
    sensor_width_mm: Optional[float] = None
    gsd_cm_per_px: Optional[float] = None

    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PresignedUploadUrlRequest(BaseModel):
    file_name: str
    mime_type: str
    file_size_bytes: int = Field(..., gt=0)
    media_type: MediaType = MediaType.IMAGE
    camera_altitude_m: Optional[float] = None
    focal_length_mm: Optional[float] = None
    sensor_width_mm: Optional[float] = None


class PresignedUploadUrlResponse(BaseModel):
    upload_url: str
    s3_key: str
    media_id: Optional[str] = None
    fields: dict = {}
    expires_in_seconds: int = 3600


class MediaUploadBatchResponse(BaseModel):
    survey_id: str
    job_id: Optional[str] = None
    uploaded_count: int
    failed_count: int
    images: List[SurveyImageResponse] = []
    errors: List[str] = []


class VideoExtractionRequest(BaseModel):
    video_id: str
    interval_seconds: float = Field(default=1.0, ge=0.1, le=60.0)
    similarity_threshold: float = Field(default=0.97, ge=0.5, le=1.0)


class MediaStatusResponse(BaseModel):
    survey_id: str
    processing_status: str
    total_images_count: int
    processed_images_count: int
    extracted_frames_count: int
    active_job_id: Optional[str] = None
    progress_percentage: int = 0
    error_message: Optional[str] = None


class SurveyResponse(SurveyBase):
    id: str
    surveyor_id: Optional[str] = None
    status: SurveyStatus
    processing_status: str = "IDLE"
    total_images_count: int = 0
    processed_images_count: int = 0
    extracted_frames_count: int = 0
    created_at: datetime
    updated_at: datetime
    images: List[SurveyImageResponse] = []

    model_config = ConfigDict(from_attributes=True)
