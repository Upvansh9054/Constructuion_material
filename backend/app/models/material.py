from sqlalchemy import (
    Boolean,
    Column,
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


class MaterialItem(Base, BaseMixin):
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

    condition_grade = Column(
        Enum(ConditionGrade),
        default=ConditionGrade.RECYCLABLE,
        nullable=False,
        index=True,
    )

    # Volumetric and Physical Quantities
    estimated_volume_m3 = Column(Float, nullable=False, default=0.0)
    estimated_weight_tonnes = Column(Float, nullable=False, default=0.0)
    unit_count = Column(Integer, nullable=True)

    # Contamination & Safety Hazards (Asbestos, Lead, Mortar, Moisture)
    contamination_risk = Column(String(255), nullable=True)

    # AI Model confidence & Spatial Metadata
    confidence_score = Column(Float, nullable=True)
    bounding_box = Column(JSON, nullable=True)  # {"x_min": float, "y_min": float, "x_max": float, "y_max": float}
    segmentation_polygon = Column(JSON, nullable=True)

    # Economic & Circular Economy Metrics
    estimated_market_value_usd = Column(Float, default=0.0, nullable=False)
    embodied_carbon_offset_kg = Column(Float, default=0.0, nullable=False)

    # Human Verification Flag
    is_verified_by_surveyor = Column(Boolean, default=False, nullable=False)
    surveyor_adjustment_notes = Column(Text, nullable=True)

    # Relationships
    survey = relationship("SiteSurvey", back_populates="material_items")
    source_image = relationship("SurveyImage", back_populates="material_items")
    marketplace_listings = relationship("MarketplaceListing", back_populates="material_item", cascade="all, delete-orphan")

