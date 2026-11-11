from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.core.constants import SurveyStatus


class SurveyBase(BaseModel):
    site_id: str
    survey_date: date
    weather_condition: Optional[str] = None
    survey_notes: Optional[str] = None


class SurveyCreate(SurveyBase):
    pass


class SurveyUpdate(BaseModel):
    weather_condition: Optional[str] = None
    survey_notes: Optional[str] = None
    status: Optional[SurveyStatus] = None


class SurveyImageResponse(BaseModel):
    id: str
    survey_id: str
    file_name: str
    original_s3_key: str
    annotated_s3_key: Optional[str] = None
    thumbnail_s3_key: Optional[str] = None
    download_url: Optional[str] = None
    file_size_bytes: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PresignedUploadUrlRequest(BaseModel):
    file_name: str
    mime_type: str
    file_size_bytes: int = Field(..., gt=0)


class PresignedUploadUrlResponse(BaseModel):
    upload_url: str
    s3_key: str
    fields: dict = {}
    expires_in_seconds: int = 3600


class SurveyResponse(SurveyBase):
    id: str
    surveyor_id: Optional[str] = None
    status: SurveyStatus
    total_images_count: int
    created_at: datetime
    updated_at: datetime
    images: List[SurveyImageResponse] = []

    class Config:
        from_attributes = True
