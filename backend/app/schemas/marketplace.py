from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
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

    model_config = ConfigDict(from_attributes=True)


class EnquiryTransactionBase(BaseModel):
    listing_id: str
    requested_tonnes: float = Field(..., gt=0.0)
    bid_price_per_tonne_usd: float = Field(..., gt=0.0)
    haulage_type: str = Field(default="FLATBED_TRAILER", max_length=100)
    notes: Optional[str] = None


class EnquiryTransactionCreate(EnquiryTransactionBase):
    pass


class EnquiryTransactionUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class EnquiryTransactionResponse(EnquiryTransactionBase):
    id: str
    buyer_id: str
    total_offer_usd: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


