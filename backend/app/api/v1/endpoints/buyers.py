from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user, record_audit_log, require_admin
from app.core.constants import AuditAction, BuyerCompanyType, UserRole
from app.core.database import get_db
from app.models.buyer import BuyerRecyclerProfile
from app.models.user import User
from app.schemas.buyer import (
    BuyerRecyclerProfileCreate,
    BuyerRecyclerProfileResponse,
    BuyerRecyclerProfileUpdate,
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[BuyerRecyclerProfileResponse])
async def list_buyer_profiles(
    search: Optional[str] = None,
    city: Optional[str] = None,
    company_type: Optional[BuyerCompanyType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List registered material buyers, scrap mills, and circular recyclers."""
    query = select(BuyerRecyclerProfile)
    if search:
        query = query.filter(
            BuyerRecyclerProfile.company_name.ilike(f"%{search}%")
            | BuyerRecyclerProfile.contact_person.ilike(f"%{search}%")
        )
    if city:
        query = query.filter(BuyerRecyclerProfile.city.ilike(f"%{city}%"))
    if company_type:
        query = query.filter(BuyerRecyclerProfile.company_type == company_type)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    query = query.order_by(BuyerRecyclerProfile.rating.desc(), BuyerRecyclerProfile.company_name).offset(offset).limit(page_size)
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


@router.get("/{profile_id}", response_model=BuyerRecyclerProfileResponse)
async def get_buyer_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed verified company profile for a buyer or recycler."""
    result = await db.execute(select(BuyerRecyclerProfile).filter(BuyerRecyclerProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer profile not found")
    return profile


@router.post("/", response_model=BuyerRecyclerProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_buyer_profile(
    profile_in: BuyerRecyclerProfileCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a verified buyer / recycler organization profile."""
    # Check if current user already has a profile
    existing = await db.execute(select(BuyerRecyclerProfile).filter(BuyerRecyclerProfile.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A buyer profile is already registered for this user account.",
        )

    profile = BuyerRecyclerProfile(
        **profile_in.model_dump(),
        user_id=current_user.id,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="BuyerRecyclerProfile",
        resource_id=profile.id,
        change_details={"company_name": profile.company_name, "company_type": profile.company_type.value},
        request=request,
    )

    return profile


@router.patch("/{profile_id}", response_model=BuyerRecyclerProfileResponse)
async def update_buyer_profile(
    profile_id: str,
    update_in: BuyerRecyclerProfileUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update company details, contact info, or accepted material streams."""
    result = await db.execute(select(BuyerRecyclerProfile).filter(BuyerRecyclerProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer profile not found")

    if profile.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, "ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this profile")

    update_dict = update_in.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(profile, k, v)

    await db.commit()
    await db.refresh(profile)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="BuyerRecyclerProfile",
        resource_id=profile.id,
        change_details=update_dict,
        request=request,
    )

    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_buyer_profile(
    profile_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """De-register a buyer or recycler profile (Admin only)."""
    result = await db.execute(select(BuyerRecyclerProfile).filter(BuyerRecyclerProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer profile not found")

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.DELETE,
        resource_type="BuyerRecyclerProfile",
        resource_id=profile.id,
        change_details={"company_name": profile.company_name},
        request=request,
    )

    await db.delete(profile)
    await db.commit()
    return None

