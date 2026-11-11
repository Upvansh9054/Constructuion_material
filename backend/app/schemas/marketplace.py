from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.core.constants import ListingStatus


class ListingBase(BaseModel):
    material_item_id: str
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    available_tonnes: float = Field(..., gt=0.0)
    min_order_tonnes: float = Field(default=1.0, gt=0.0)
    price_per_tonne_usd: float = Field(..., gt=0.0)
    pickup_address: str = Field(..., min_length=5, max_length=500)
    pickup_city: str = Field(..., min_length=2, max_length=100)
    logistics_notes: Optional[str] = None


class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    available_tonnes: Optional[float] = Field(None, gt=0.0)
    min_order_tonnes: Optional[float] = Field(None, gt=0.0)
    price_per_tonne_usd: Optional[float] = Field(None, gt=0.0)
    pickup_address: Optional[str] = None
    pickup_city: Optional[str] = None
    logistics_notes: Optional[str] = None
    status: Optional[ListingStatus] = None


class ListingResponse(ListingBase):
    id: str
    seller_id: str
    total_price_usd: float
    status: ListingStatus
    listed_at: Optional[datetime] = None
    sold_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

