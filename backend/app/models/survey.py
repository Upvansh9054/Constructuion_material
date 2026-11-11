from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.constants import MediaType, SurveyStatus
from app.models.base import BaseMixin


class SiteSurvey(Base, BaseMixin):
    __tablename__ = "site_surveys"

    site_id = Column(
        String(36),
        ForeignKey("demolition_sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    surveyor_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    survey_date = Column(Date, nullable=False)
    weather_condition = Column(String(100), nullable=True)
    survey_notes = Column(Text, nullable=True)
    status = Column(
        Enum(SurveyStatus), default=SurveyStatus.PENDING, nullable=False, index=True
    )
    total_images_count = Column(Integer, default=0, nullable=False)

    # Relationships
    site = relationship("DemolitionSite", back_populates="surveys")
    surveyor = relationship("User", back_populates="surveys")
    images = relationship(
        "SurveyImage", back_populates="survey", cascade="all, delete-orphan", lazy="selectin"
    )
    material_items = relationship(
        "MaterialItem", back_populates="survey", cascade="all, delete-orphan"
    )
    analysis_jobs = relationship(
        "AnalysisJob", back_populates="survey", cascade="all, delete-orphan"
    )
    audit_reports = relationship(
        "DemolitionAuditReport",
        back_populates="survey",
        cascade="all, delete-orphan",
    )


class SurveyImage(Base, BaseMixin):
    __tablename__ = "survey_images"

    survey_id = Column(
        String(36),
        ForeignKey("site_surveys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name = Column(String(255), nullable=False)
    media_type = Column(Enum(MediaType), default=MediaType.IMAGE, nullable=False)
    original_s3_key = Column(String(500), nullable=False)
    annotated_s3_key = Column(String(500), nullable=True)
    thumbnail_s3_key = Column(String(500), nullable=True)

    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    # Photogrammetry & Camera Calibration Parameters
    camera_altitude_m = Column(Float, nullable=True)
    focal_length_mm = Column(Float, nullable=True)
    sensor_width_mm = Column(Float, nullable=True)
    gsd_cm_per_px = Column(Float, nullable=True)

    # Geolocation if extracted from image EXIF
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)

    # Relationships
    survey = relationship("SiteSurvey", back_populates="images")
    material_items = relationship("MaterialItem", back_populates="source_image")
