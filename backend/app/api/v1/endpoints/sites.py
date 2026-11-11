from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.site import DemolitionSite
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.site import SiteCreate, SiteResponse, SiteUpdate

router = APIRouter()


@router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_demolition_site(
    site_in: SiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new demolition site survey project."""
    # Check if site_code is already used
    existing = await db.execute(select(DemolitionSite).filter(DemolitionSite.site_code == site_in.site_code))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Site code '{site_in.site_code}' is already registered.",
        )

    site = DemolitionSite(
        **site_in.model_dump(),
        contractor_id=current_user.id,
    )
    db.add(site)
    await db.commit()
    await db.refresh(site)
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update demolition site metadata or status."""
    result = await db.execute(select(DemolitionSite).filter(DemolitionSite.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    update_data = site_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(site, field, val)

    await db.commit()
    await db.refresh(site)
    return site

