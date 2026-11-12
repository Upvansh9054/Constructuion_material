from datetime import datetime
from typing import Any, Dict, List, Optional
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
    dimension_length_m: Optional[float] = None
    dimension_width_m: Optional[float] = None
    dimension_height_m: Optional[float] = None
    surface_area_m2: Optional[float] = None
    min_volume_m3: Optional[float] = None
    max_volume_m3: Optional[float] = None
    min_weight_tonnes: Optional[float] = None
    max_weight_tonnes: Optional[float] = None
    uncertainty_percentage: float = Field(default=20.0, ge=0.0, le=100.0)
    assumed_density_t_per_m3: float = Field(default=2.40, ge=0.1, le=20.0)
    packing_factor: float = Field(default=0.85, ge=0.1, le=1.0)
    calculation_method: str = Field(default="calibrated_gsd_photogrammetry")
    reference_measurement_notes: Optional[str] = None
    unit_count: Optional[int] = Field(default=None, ge=0)
    contamination_risk: Optional[str] = None
    damage_severity_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    damage_type: Optional[str] = None
    requires_specialist_abatement: bool = False
    hazard_inspection_warning: Optional[str] = None
    recommended_recovery_route: str = "CLOSED_LOOP_RECYCLING"
    recoverability_percentage: float = Field(default=85.0, ge=0.0, le=100.0)


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
    dimension_length_m: Optional[float] = None
    dimension_width_m: Optional[float] = None
    dimension_height_m: Optional[float] = None
    surface_area_m2: Optional[float] = None
    min_volume_m3: Optional[float] = None
    max_volume_m3: Optional[float] = None
    min_weight_tonnes: Optional[float] = None
    max_weight_tonnes: Optional[float] = None
    uncertainty_percentage: Optional[float] = None
    assumed_density_t_per_m3: Optional[float] = None
    unit_count: Optional[int] = Field(None, ge=0)
    packing_factor: Optional[float] = Field(None, ge=0.1, le=1.0)
    contamination_risk: Optional[str] = None
    damage_severity_pct: Optional[float] = None
    damage_type: Optional[str] = None
    requires_specialist_abatement: Optional[bool] = None
    hazard_inspection_warning: Optional[str] = None
    recommended_recovery_route: Optional[str] = None
    recoverability_percentage: Optional[float] = None
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
    verified_weight_tonnes: Optional[float] = None
    verified_volume_m3: Optional[float] = None
    weighbridge_ticket_number: Optional[str] = None
    weighbridge_scale_id: Optional[str] = None
    weighbridge_timestamp: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuantityEstimationRequest(BaseModel):
    category: MaterialCategory
    detection_box: Optional[BoundingBox] = None
    image_width: int = Field(default=1920, ge=100)
    image_height: int = Field(default=1080, ge=100)
    camera_height_m: Optional[float] = Field(None, ge=0.5, le=500.0)
    focal_length_mm: Optional[float] = Field(None, ge=1.0, le=500.0)
    sensor_width_mm: Optional[float] = Field(None, ge=1.0, le=100.0)
    reference_measurement_m: Optional[float] = Field(None, ge=0.01, le=100.0)
    reference_pixel_length: Optional[float] = Field(None, ge=1.0)
    manual_length_m: Optional[float] = Field(None, ge=0.01)
    manual_width_m: Optional[float] = Field(None, ge=0.01)
    manual_height_m: Optional[float] = Field(None, ge=0.01)
    custom_density_t_per_m3: Optional[float] = Field(None, ge=0.1, le=25.0)
    custom_packing_factor: Optional[float] = Field(None, ge=0.1, le=1.0)


class QuantityEstimationResponse(BaseModel):
    nominal_volume_m3: float
    nominal_weight_tonnes: float
    min_volume_m3: float
    max_volume_m3: float
    min_weight_tonnes: float
    max_weight_tonnes: float
    uncertainty_percentage: float
    dimension_length_m: float
    dimension_width_m: float
    dimension_height_m: float
    surface_area_m2: float
    assumed_density_t_per_m3: float
    packing_factor: float
    estimation_method: str
    assumptions_applied: Dict[str, Any] = {}


class MaterialConditionAssessmentRequest(BaseModel):
    category: MaterialCategory
    building_year: Optional[int] = Field(None, ge=1800, le=2050)
    site_has_asbestos_risk: bool = False
    site_has_lead_paint: bool = False
    manual_hazard_flags: List[str] = []
    crop_image_bytes_base64: Optional[str] = None


class MaterialConditionAssessmentResponse(BaseModel):
    grade: ConditionGrade
    damage_severity_pct: float
    damage_type: Optional[str] = None
    contamination_risk: Optional[str] = None
    requires_specialist_abatement: bool
    hazard_inspection_warning: Optional[str] = None
    recommended_recovery_route: str
    recoverability_percentage: float
    inspection_notes: str
    confidence: float
    indicators: List[str] = []


class WeighbridgeVerificationRequest(BaseModel):
    verified_weight_tonnes: float = Field(..., ge=0.0, description="Certified weighbridge scale measurement in tonnes")
    verified_volume_m3: Optional[float] = Field(None, ge=0.0)
    weighbridge_ticket_number: str = Field(..., min_length=2, max_length=100)
    weighbridge_scale_id: Optional[str] = Field(None, max_length=100)
    weighbridge_timestamp: Optional[datetime] = None
    surveyor_notes: Optional[str] = None


class WeighbridgeVerificationResponse(BaseModel):
    material_item_id: str
    estimated_weight_tonnes: float
    verified_weight_tonnes: float
    weight_delta_tonnes: float
    weight_variance_percentage: float
    weighbridge_ticket_number: str
    is_verified: bool
    verified_by_user_id: str
    verified_at: datetime


class AssumptionsDefaultsResponse(BaseModel):
    densities: Dict[str, Dict[str, float]]
    packing_factors: Dict[str, Dict[str, float]]
    depth_priors: Dict[str, Dict[str, float]]
    regulatory_guidance: Dict[str, str]


class StereoReconstructionRequest(BaseModel):
    image_a_id: Optional[str] = None
    image_b_id: Optional[str] = None
    image_a_base64: Optional[str] = None
    image_b_base64: Optional[str] = None
    focal_length_mm: Optional[float] = Field(None, ge=1.0, le=500.0)
    sensor_width_mm: Optional[float] = Field(None, ge=1.0, le=100.0)
    baseline_distance_m: Optional[float] = Field(None, ge=0.01, le=100.0)
    camera_height_m: Optional[float] = Field(None, ge=0.5, le=500.0)


class StereoReconstructionResponse(BaseModel):
    point_count: int
    bounding_box_3d: Dict[str, float]
    convex_hull_volume_m3: float
    reconstruction_confidence: float
    matched_features_count: int
    triangulation_error_px: float
    methodology_used: str
    point_cloud_summary: Dict[str, Any] = {}


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
