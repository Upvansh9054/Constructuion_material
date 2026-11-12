from sqlalchemy import Boolean, Column, Date, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.constants import SiteStatus
from app.models.base import BaseMixin


class DemolitionSite(Base, BaseMixin):
    __tablename__ = "demolition_sites"

    name = Column(String(255), nullable=False, index=True)
    site_code = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="USA", nullable=False)
    
    # Geo-coordinates for spatial mapping & logistics
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Site information & structural attributes
    building_type = Column(String(100), nullable=True)  # e.g. Industrial, Commercial, Residential, Warehouse
    building_length_m = Column(Float, nullable=True)
    building_width_m = Column(Float, nullable=True)
    building_height_m = Column(Float, nullable=True)
    number_of_floors = Column(Integer, nullable=True)
    total_building_volume_m3 = Column(Float, nullable=True)
    footprint_sqm = Column(Float, nullable=True)
    structural_type = Column(String(150), nullable=True)  # e.g. "Steel Frame & Concrete Shear Wall"
    has_asbestos_risk = Column(Boolean, default=False, nullable=False)
    has_lead_paint = Column(Boolean, default=False, nullable=False)
    hazard_notes = Column(Text, nullable=True)

    status = Column(Enum(SiteStatus), default=SiteStatus.PLANNING, nullable=False, index=True)
    estimated_demolition_date = Column(Date, nullable=True)
    actual_demolition_date = Column(Date, nullable=True)

    # Ownership & Foreign Keys
    contractor_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    contractor = relationship("User", back_populates="sites")

    # Associated Surveys & Reports
    surveys = relationship("SiteSurvey", back_populates="site", cascade="all, delete-orphan")
    reports = relationship("DemolitionAuditReport", back_populates="site", cascade="all, delete-orphan")
