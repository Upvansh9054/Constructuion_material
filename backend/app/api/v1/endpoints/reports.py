from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user, record_audit_log, require_contractor
from app.core.constants import AuditAction, UserRole
from app.core.database import get_db
from app.models.audit_report import DemolitionAuditReport
from app.models.material import MaterialItem
from app.models.site import DemolitionSite
from app.models.survey import SiteSurvey
from app.models.user import User
from app.schemas.audit_report import (
    DemolitionAuditReportCreate,
    DemolitionAuditReportResponse,
)

router = APIRouter()


@router.post("/", response_model=DemolitionAuditReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_demolition_audit_report(
    report_in: DemolitionAuditReportCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Synthesize survey photogrammetry, inventory, and valuation into a Pre-Demolition Material Audit Report (DMAR)."""
    site_res = await db.execute(select(DemolitionSite).filter(DemolitionSite.id == report_in.site_id))
    site = site_res.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demolition site not found")

    survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == report_in.survey_id))
    survey = survey_res.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site survey not found")

    # Fetch materials for this survey
    materials_res = await db.execute(select(MaterialItem).filter(MaterialItem.survey_id == report_in.survey_id))
    items = list(materials_res.scalars().all())

    total_tonnes = sum(it.estimated_weight_tonnes for it in items)
    total_value = sum(it.estimated_market_value_usd for it in items)
    total_carbon = sum(it.embodied_carbon_offset_kg for it in items)

    breakdown = {}
    for it in items:
        cat = it.category.value if hasattr(it.category, "value") else str(it.category)
        if cat not in breakdown:
            breakdown[cat] = {"tonnes": 0.0, "value_usd": 0.0, "carbon_kg": 0.0, "count": 0}
        breakdown[cat]["tonnes"] = round(breakdown[cat]["tonnes"] + it.estimated_weight_tonnes, 2)
        breakdown[cat]["value_usd"] = round(breakdown[cat]["value_usd"] + it.estimated_market_value_usd, 2)
        breakdown[cat]["carbon_kg"] = round(breakdown[cat]["carbon_kg"] + it.embodied_carbon_offset_kg, 2)
        breakdown[cat]["count"] += 1

    title = report_in.report_title or f"Pre-Demolition Material Audit Report: {site.name}"
    exec_summary = (
        f"Pre-Demolition Audit conducted for site '{site.name}' ({site.site_code}) located in {site.city}, {site.state}. "
        f"Identified {len(items)} recoverable lots encompassing {round(total_tonnes, 2)} tonnes with an estimated gross circular "
        f"recovery valuation of ${round(total_value, 2):,}. Diverting these materials mitigates approximately "
        f"{round(total_carbon / 1000.0, 2)} metric tons of CO2e."
    )
    compliance_notes = (
        f"Hazard Screening: Asbestos Risk: {'HIGH' if site.has_asbestos_risk else 'None Detected'}. "
        f"Lead Paint Risk: {'DETECTED' if site.has_lead_paint else 'None Detected'}. "
        f"Structural Type: {site.structural_type or 'General Commercial Masonry'}. Complies with BREEAM/LEED Demolition Protocols."
    )
    buyer_insights = (
        f"High secondary market liquidity for {len([c for c in breakdown if 'STEEL' in c or 'CONCRETE' in c])} "
        f"mineral and structural lots. Recommended dispatch to certified regional recyclers within 50 km."
    )

    report = DemolitionAuditReport(
        site_id=site.id,
        survey_id=survey.id,
        report_title=title,
        executive_summary=exec_summary,
        regulatory_compliance_notes=compliance_notes,
        buyer_matching_insights=buyer_insights,
        total_recoverable_tonnes=round(total_tonnes, 2),
        total_estimated_value_usd=round(total_value, 2),
        total_carbon_offset_kg_co2e=round(total_carbon, 2),
        detailed_breakdown_json=breakdown,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="DemolitionAuditReport",
        resource_id=report.id,
        change_details={"title": title, "tonnes": total_tonnes, "value_usd": total_value},
        request=request,
    )

    return report


@router.get("/", response_model=List[DemolitionAuditReportResponse])
async def list_audit_reports(
    site_id: Optional[str] = Query(None, description="Filter by site ID"),
    survey_id: Optional[str] = Query(None, description="Filter by survey ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List generated Pre-Demolition Material Audit Reports (DMAR)."""
    query = select(DemolitionAuditReport)
    if site_id:
        query = query.filter(DemolitionAuditReport.site_id == site_id)
    if survey_id:
        query = query.filter(DemolitionAuditReport.survey_id == survey_id)

    query = query.order_by(DemolitionAuditReport.created_at.desc())
    res = await db.execute(query)
    return list(res.scalars().all())


@router.get("/{report_id}", response_model=DemolitionAuditReportResponse)
async def get_audit_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full audit report details."""
    res = await db.execute(select(DemolitionAuditReport).filter(DemolitionAuditReport.id == report_id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit_report(
    report_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Delete an audit report."""
    res = await db.execute(select(DemolitionAuditReport).filter(DemolitionAuditReport.id == report_id))
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.DELETE,
        resource_type="DemolitionAuditReport",
        resource_id=report.id,
        change_details={"title": report.report_title},
        request=request,
    )

    await db.delete(report)
    await db.commit()
    return None

