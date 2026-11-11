from sqlalchemy import Column, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseMixin


class DemolitionAuditReport(Base, BaseMixin):
    __tablename__ = "demolition_audit_reports"

    site_id = Column(
        String(36),
        ForeignKey("demolition_sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    survey_id = Column(
        String(36),
        ForeignKey("site_surveys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    report_title = Column(String(255), nullable=False)
    executive_summary = Column(Text, nullable=False)
    regulatory_compliance_notes = Column(Text, nullable=True)
    buyer_matching_insights = Column(Text, nullable=True)

    total_recoverable_tonnes = Column(Float, default=0.0, nullable=False)
    total_estimated_value_usd = Column(Float, default=0.0, nullable=False)
    total_carbon_offset_kg_co2e = Column(Float, default=0.0, nullable=False)

    detailed_breakdown_json = Column(JSON, nullable=False)  # Category-wise volume, weight, condition distribution
    pdf_report_s3_key = Column(String(500), nullable=True)

    # Relationships
    site = relationship("DemolitionSite", back_populates="reports")
    survey = relationship("SiteSurvey", back_populates="audit_reports")
