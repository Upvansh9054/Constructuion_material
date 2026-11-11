from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class DemolitionAuditReportBase(BaseModel):
    site_id: str
    survey_id: str
    report_title: str = Field(..., min_length=3, max_length=255)
    executive_summary: str
    regulatory_compliance_notes: Optional[str] = None
    buyer_matching_insights: Optional[str] = None
    total_recoverable_tonnes: float = 0.0
    total_estimated_value_usd: float = 0.0
    total_carbon_offset_kg_co2e: float = 0.0
    detailed_breakdown_json: Dict[str, Any] = Field(default_factory=dict)
    pdf_report_s3_key: Optional[str] = None


class DemolitionAuditReportCreate(BaseModel):
    site_id: str
    survey_id: str
    report_title: Optional[str] = None


class DemolitionAuditReportResponse(DemolitionAuditReportBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
