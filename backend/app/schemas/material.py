from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.constants import ConditionGrade, MaterialCategory


class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class MaterialCategoryDefinitionResponse(BaseModel):
    category: MaterialCategory
    name: str
    description: Optional[str] = None
    standard_density_t_per_m3: float
    carbon_offset_factor_kg_per_t: float
    default_price_per_t_usd: float
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class MaterialItemBase(BaseModel):
    category: MaterialCategory
    subcategory: Optional[str] = None
    description: Optional[str] = None
    condition_grade: ConditionGrade = ConditionGrade.RECYCLABLE
    estimated_volume_m3: float = Field(default=0.0, ge=0.0)
    estimated_weight_tonnes: float = Field(default=0.0, ge=0.0)
    unit_count: Optional[int] = Field(default=None, ge=0)
    packing_factor: float = Field(default=0.85, ge=0.1, le=1.0)
    calculation_method: str = Field(default="calibrated_gsd_photogrammetry")
    contamination_risk: Optional[str] = None


class MaterialItemCreate(MaterialItemBase):
    survey_id: str
    source_image_id: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    bounding_box: Optional[BoundingBox] = None


class MaterialItemUpdate(BaseModel):
    category: Optional[MaterialCategory] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    condition_grade: Optional[ConditionGrade] = None
    estimated_volume_m3: Optional[float] = Field(None, ge=0.0)
    estimated_weight_tonnes: Optional[float] = Field(None, ge=0.0)
    unit_count: Optional[int] = Field(None, ge=0)
    packing_factor: Optional[float] = Field(None, ge=0.1, le=1.0)
    contamination_risk: Optional[str] = None
    is_verified_by_surveyor: Optional[bool] = None
    surveyor_adjustment_notes: Optional[str] = None


class MaterialItemResponse(MaterialItemBase):
    id: str
    survey_id: str
    source_image_id: Optional[str] = None
    confidence_score: Optional[float] = None
    bounding_box: Optional[Dict[str, float]] = None
    estimated_market_value_usd: float
    embodied_carbon_offset_kg: float
    is_verified_by_surveyor: bool
    surveyor_adjustment_notes: Optional[str] = None
    verified_by_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaterialCategorySummary(BaseModel):
    category: MaterialCategory
    total_volume_m3: float
    total_weight_tonnes: float
    estimated_value_usd: float
    carbon_offset_kg_co2e: float
    item_count: int


class ValuationSummary(BaseModel):
    total_estimated_value_usd: float
    total_recoverable_tonnes: float
    total_carbon_offset_kg_co2e: float
    categories: List[MaterialCategorySummary]
