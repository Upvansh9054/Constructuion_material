from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.core.constants import SiteStatus


class SiteBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    site_code: str = Field(..., min_length=2, max_length=64)
    description: Optional[str] = None
    address: str = Field(..., min_length=5, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    postal_code: Optional[str] = None
    country: str = Field(default="USA", max_length=100)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    status: SiteStatus = SiteStatus.PLANNING
    estimated_demolition_date: Optional[date] = None


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: Optional[SiteStatus] = None
    estimated_demolition_date: Optional[date] = None
    actual_demolition_date: Optional[date] = None


class SiteResponse(SiteBase):
    id: str
    contractor_id: str
    actual_demolition_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
