from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user
from app.core.constants import ListingStatus
from app.core.database import get_db
from app.models.marketplace import MarketplaceListing
from app.models.material import MaterialItem
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.marketplace import ListingCreate, ListingResponse, ListingUpdate

router = APIRouter()


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_marketplace_listing(
    listing_in: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recovered materials on the marketplace for secondary buyers and recyclers."""
    # Check material exists
    item_result = await db.execute(select(MaterialItem).filter(MaterialItem.id == listing_in.material_item_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material item not found")

    total_price = round(listing_in.available_tonnes * listing_in.price_per_tonne_usd, 2)

    listing = MarketplaceListing(
        **listing_in.model_dump(),
        seller_id=current_user.id,
        total_price_usd=total_price,
        status=ListingStatus.ACTIVE,
        listed_at=datetime.now(timezone.utc),
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return listing


@router.get("/", response_model=PaginatedResponse[ListingResponse])
async def list_marketplace_offers(
    city: Optional[str] = None,
    status_filter: Optional[ListingStatus] = ListingStatus.ACTIVE,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Browse available recovered construction materials for purchase."""
    query = select(MarketplaceListing)
    if status_filter:
        query = query.filter(MarketplaceListing.status == status_filter)
    if city:
        query = query.filter(MarketplaceListing.pickup_city.ilike(f"%{city}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    query = query.order_by(MarketplaceListing.listed_at.desc()).offset(offset).limit(page_size)
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


@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing_status(
    listing_id: str,
    update_in: ListingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update listing price, quantity, or mark as RESERVED/SOLD."""
    result = await db.execute(select(MarketplaceListing).filter(MarketplaceListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    if listing.seller_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this listing")

    update_dict = update_in.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(listing, k, v)

    if "available_tonnes" in update_dict or "price_per_tonne_usd" in update_dict:
        listing.total_price_usd = round(listing.available_tonnes * listing.price_per_tonne_usd, 2)

    if update_in.status == ListingStatus.SOLD and not listing.sold_at:
        listing.sold_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(listing)
    return listing
