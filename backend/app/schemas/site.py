from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.constants import SiteStatus


class SiteBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Project / facility name")
    site_code: str = Field(..., min_length=2, max_length=64, description="Unique project code")
    description: Optional[str] = None
    address: str = Field(..., min_length=5, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = None
    country: str = Field(default="USA", max_length=100)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    
    # Site information & structural attributes
    footprint_sqm: Optional[float] = Field(None, ge=0.0, description="Gross structural area")
    structural_type: Optional[str] = None
    has_asbestos_risk: bool = Field(default=False)
    has_lead_paint: bool = Field(default=False)
    hazard_notes: Optional[str] = None

    status: SiteStatus = SiteStatus.PLANNING
    estimated_demolition_date: Optional[date] = None


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    footprint_sqm: Optional[float] = None
    structural_type: Optional[str] = None
    has_asbestos_risk: Optional[bool] = None
    has_lead_paint: Optional[bool] = None
    hazard_notes: Optional[str] = None
    status: Optional[SiteStatus] = None
    estimated_demolition_date: Optional[date] = None
    actual_demolition_date: Optional[date] = None


class SiteResponse(SiteBase):
    id: str
    contractor_id: str
    actual_demolition_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
