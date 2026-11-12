from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user, record_audit_log, require_contractor
from app.core.constants import AuditAction, UserRole
from app.core.database import get_db
from app.models.site import DemolitionSite
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.site import SiteCreate, SiteResponse, SiteUpdate

router = APIRouter()


@router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_demolition_site(
    site_in: SiteCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Create a new demolition site survey project (Contractor or Admin)."""
    # Check if site_code is already used
    existing = await db.execute(select(DemolitionSite).filter(DemolitionSite.site_code == site_in.site_code))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Site code '{site_in.site_code}' is already registered.",
        )

    site_data = site_in.model_dump()
    if (
        not site_data.get("total_building_volume_m3")
        and site_data.get("building_length_m")
        and site_data.get("building_width_m")
        and site_data.get("building_height_m")
    ):
        site_data["total_building_volume_m3"] = round(
            float(site_data["building_length_m"])
            * float(site_data["building_width_m"])
            * float(site_data["building_height_m"]),
            2,
        )

    site = DemolitionSite(
        **site_data,
        contractor_id=current_user.id,
    )
    db.add(site)
    await db.commit()
    await db.refresh(site)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="DemolitionSite",
        resource_id=site.id,
        change_details={"site_code": site.site_code, "name": site.name, "city": site.city},
        request=request,
    )

    return site


@router.get("/", response_model=PaginatedResponse[SiteResponse])
async def list_demolition_sites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List demolition sites with pagination and search."""
    query = select(DemolitionSite)
    if search:
        query = query.filter(DemolitionSite.name.ilike(f"%{search}%") | DemolitionSite.site_code.ilike(f"%{search}%"))
    if city:
        query = query.filter(DemolitionSite.city.ilike(f"%{city}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(DemolitionSite.created_at.desc()).offset(offset).limit(page_size)
    items_result = await db.execute(query)
    items = list(items_result.scalars().all())

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site_details(
    site_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get demolition site details by ID."""
    result = await db.execute(select(DemolitionSite).filter(DemolitionSite.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return site


@router.patch("/{site_id}", response_model=SiteResponse)
async def update_site_details(
    site_id: str,
    site_update: SiteUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Update demolition site metadata or status."""
    result = await db.execute(select(DemolitionSite).filter(DemolitionSite.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    # Only project contractor or admin can update
    if site.contractor_id != current_user.id and current_user.role not in [UserRole.ADMIN, "ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this site.")

    update_data = site_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(site, field, val)

    await db.commit()
    await db.refresh(site)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="DemolitionSite",
        resource_id=site.id,
        change_details=update_data,
        request=request,
    )

    return site


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_demolition_site(
    site_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Delete a demolition site project (Contractor owner or Admin)."""
    result = await db.execute(select(DemolitionSite).filter(DemolitionSite.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    if site.contractor_id != current_user.id and current_user.role not in [UserRole.ADMIN, "ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this site.")

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.DELETE,
        resource_type="DemolitionSite",
        resource_id=site.id,
        change_details={"name": site.name, "site_code": site.site_code},
        request=request,
    )

    await db.delete(site)
    await db.commit()
    return None
