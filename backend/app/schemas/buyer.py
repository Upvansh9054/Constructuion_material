from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.core.constants import BuyerCompanyType


class BuyerRecyclerProfileBase(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    company_type: BuyerCompanyType = BuyerCompanyType.STEEL_MILL
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    distance_km: float = Field(default=25.0, ge=0.0)
    accepted_categories: List[str] = Field(default_factory=list)
    certified_standards: List[str] = Field(default_factory=list)
    contact_person: str = Field(..., min_length=2, max_length=150)
    contact_email: EmailStr
    contact_phone: str = Field(..., min_length=5, max_length=50)


class BuyerRecyclerProfileCreate(BuyerRecyclerProfileBase):
    pass


class BuyerRecyclerProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    company_type: Optional[BuyerCompanyType] = None
    city: Optional[str] = None
    state: Optional[str] = None
    distance_km: Optional[float] = None
    accepted_categories: Optional[List[str]] = None
    certified_standards: Optional[List[str]] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class BuyerRecyclerProfileResponse(BuyerRecyclerProfileBase):
    id: str
    user_id: str
    total_purchased_tonnes: float
    active_bids_count: int
    rating: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
