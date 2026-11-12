from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.constants import ConditionGrade, MaterialCategory
from app.models.base import BaseMixin


class MaterialCategoryDefinition(Base, BaseMixin):
    """Module 7: Material Category Definitions & Reference Standards."""
    __tablename__ = "material_category_definitions"

    category = Column(Enum(MaterialCategory), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    standard_density_t_per_m3 = Column(Float, nullable=False)
    carbon_offset_factor_kg_per_t = Column(Float, nullable=False)
    default_price_per_t_usd = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class MaterialItem(Base, BaseMixin):
    """Modules 8, 9, 10: Material Inventory, Quantity Estimates, and Recovery Assessments."""
    __tablename__ = "material_items"

    survey_id = Column(
        String(36),
        ForeignKey("site_surveys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_image_id = Column(
        String(36),
        ForeignKey("survey_images.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    category = Column(Enum(MaterialCategory), nullable=False, index=True)
    subcategory = Column(String(150), nullable=True)  # e.g. "Structural Steel I-Beam", "Clay Facing Bricks"
    description = Column(Text, nullable=True)

    # Module 10: Recovery Assessment - Condition Grade
    condition_grade = Column(
        Enum(ConditionGrade),
        default=ConditionGrade.RECYCLABLE,
        nullable=False,
        index=True,
    )

    # Module 9: Volumetric, Dimensional, and Physical Quantities
    estimated_volume_m3 = Column(Float, nullable=False, default=0.0)
    estimated_weight_tonnes = Column(Float, nullable=False, default=0.0)
    dimension_length_m = Column(Float, nullable=True)
    dimension_width_m = Column(Float, nullable=True)
    dimension_height_m = Column(Float, nullable=True)
    surface_area_m2 = Column(Float, nullable=True)

    # Uncertainty boundaries (±%)
    min_volume_m3 = Column(Float, nullable=True)
    max_volume_m3 = Column(Float, nullable=True)
    min_weight_tonnes = Column(Float, nullable=True)
    max_weight_tonnes = Column(Float, nullable=True)
    uncertainty_percentage = Column(Float, default=20.0, nullable=False)

    # Configurable assumptions applied
    assumed_density_t_per_m3 = Column(Float, default=2.40, nullable=False)
    packing_factor = Column(Float, default=0.85, nullable=False)
    calculation_method = Column(String(100), default="calibrated_gsd_photogrammetry", nullable=False)
    reference_measurement_notes = Column(String(255), nullable=True)
    unit_count = Column(Integer, nullable=True)

    # Contamination & Safety Hazards (Asbestos ACM, Lead, Creosote, Mortar)
    contamination_risk = Column(String(255), nullable=True)
    damage_severity_pct = Column(Float, default=0.0, nullable=False)
    damage_type = Column(String(100), nullable=True)
    requires_specialist_abatement = Column(Boolean, default=False, nullable=False)
    hazard_inspection_warning = Column(Text, nullable=True)

    # Recoverability & Circular Economy
    recommended_recovery_route = Column(String(100), default="CLOSED_LOOP_RECYCLING", nullable=False)
    recoverability_percentage = Column(Float, default=85.0, nullable=False)

    # AI Model confidence & Spatial Metadata
    confidence_score = Column(Float, nullable=True)
    bounding_box = Column(JSON, nullable=True)  # {"x_min": float, "y_min": float, "x_max": float, "y_max": float}
    segmentation_polygon = Column(JSON, nullable=True)

    # Economic & Circular Economy Valuation Metrics
    estimated_market_value_usd = Column(Float, default=0.0, nullable=False)
    embodied_carbon_offset_kg = Column(Float, default=0.0, nullable=False)

    # Human Surveyor Verification & Certified Weighbridge Storage (Stored Separately)
    is_verified_by_surveyor = Column(Boolean, default=False, nullable=False, index=True)
    surveyor_adjustment_notes = Column(Text, nullable=True)
    verified_by_user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_weight_tonnes = Column(Float, nullable=True)
    verified_volume_m3 = Column(Float, nullable=True)
    weighbridge_ticket_number = Column(String(100), nullable=True)
    weighbridge_scale_id = Column(String(100), nullable=True)
    weighbridge_timestamp = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    survey = relationship("SiteSurvey", back_populates="material_items")
    source_image = relationship("SurveyImage", back_populates="material_items")
    marketplace_listings = relationship("MarketplaceListing", back_populates="material_item", cascade="all, delete-orphan")
