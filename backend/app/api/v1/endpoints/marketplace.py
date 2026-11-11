from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user, record_audit_log, require_buyer, require_contractor
from app.core.constants import AuditAction, ListingStatus, TransactionStatus, UserRole
from app.core.database import get_db
from app.models.marketplace import EnquiryTransaction, MarketplaceListing
from app.models.material import MaterialItem
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.marketplace import (
    EnquiryTransactionCreate,
    EnquiryTransactionResponse,
    EnquiryTransactionUpdate,
    ListingCreate,
    ListingResponse,
    ListingUpdate,
)

router = APIRouter()


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_marketplace_listing(
    listing_in: ListingCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """List recovered materials on the marketplace for secondary buyers and recyclers."""
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

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="MarketplaceListing",
        resource_id=listing.id,
        change_details={"title": listing.title, "tonnes": listing.available_tonnes, "price_usd": total_price},
        request=request,
    )

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


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_marketplace_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single marketplace listing by ID."""
    result = await db.execute(select(MarketplaceListing).filter(MarketplaceListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing


@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing_status(
    listing_id: str,
    update_in: ListingUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update listing price, quantity, or mark as RESERVED/SOLD."""
    result = await db.execute(select(MarketplaceListing).filter(MarketplaceListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    if listing.seller_id != current_user.id and current_user.role not in [UserRole.ADMIN, "ADMIN"]:
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

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="MarketplaceListing",
        resource_id=listing.id,
        change_details=update_dict,
        request=request,
    )

    return listing


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete or withdraw a marketplace listing."""
    result = await db.execute(select(MarketplaceListing).filter(MarketplaceListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    if listing.seller_id != current_user.id and current_user.role not in [UserRole.ADMIN, "ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this listing")

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.DELETE,
        resource_type="MarketplaceListing",
        resource_id=listing.id,
        change_details={"title": listing.title},
        request=request,
    )

    await db.delete(listing)
    await db.commit()
    return None


# Module 13: Enquiries & Transactions


@router.post("/{listing_id}/bids", response_model=EnquiryTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_enquiry_bid(
    listing_id: str,
    bid_in: EnquiryTransactionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_buyer),
):
    """Place a commercial purchase offer or recycling enquiry on a listing."""
    result = await db.execute(select(MarketplaceListing).filter(MarketplaceListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    if listing.status != ListingStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Listing is not active for bids.")

    if bid_in.requested_tonnes > listing.available_tonnes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested quantity ({bid_in.requested_tonnes} t) exceeds available ({listing.available_tonnes} t).",
        )

    total_offer = round(bid_in.requested_tonnes * bid_in.bid_price_per_tonne_usd, 2)

    transaction = EnquiryTransaction(
        listing_id=listing_id,
        buyer_id=current_user.id,
        requested_tonnes=bid_in.requested_tonnes,
        bid_price_per_tonne_usd=bid_in.bid_price_per_tonne_usd,
        total_offer_usd=total_offer,
        haulage_type=bid_in.haulage_type,
        status=TransactionStatus.PENDING,
        notes=bid_in.notes,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="EnquiryTransaction",
        resource_id=transaction.id,
        change_details={"listing_id": listing_id, "tonnes": transaction.requested_tonnes, "offer_usd": total_offer},
        request=request,
    )

    return transaction


@router.get("/{listing_id}/bids", response_model=List[EnquiryTransactionResponse])
async def list_listing_bids(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List bids placed on a listing (seller, admin, or individual buyer bids)."""
    result = await db.execute(select(MarketplaceListing).filter(MarketplaceListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    query = select(EnquiryTransaction).filter(EnquiryTransaction.listing_id == listing_id)
    if listing.seller_id != current_user.id and current_user.role not in [UserRole.ADMIN, "ADMIN"]:
        # Regular users can only see their own bids
        query = query.filter(EnquiryTransaction.buyer_id == current_user.id)

    query = query.order_by(EnquiryTransaction.created_at.desc())
    bids_result = await db.execute(query)
    return list(bids_result.scalars().all())


@router.get("/bids/my", response_model=List[EnquiryTransactionResponse])
async def list_my_bids(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all bids/enquiries submitted by the currently logged-in buyer."""
    query = (
        select(EnquiryTransaction)
        .filter(EnquiryTransaction.buyer_id == current_user.id)
        .order_by(EnquiryTransaction.created_at.desc())
    )
    bids_result = await db.execute(query)
    return list(bids_result.scalars().all())


@router.patch("/bids/{bid_id}/status", response_model=EnquiryTransactionResponse)
async def update_bid_status(
    bid_id: str,
    update_in: EnquiryTransactionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept, reject, or complete a material bid (Contractor or Admin)."""
    result = await db.execute(select(EnquiryTransaction).filter(EnquiryTransaction.id == bid_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction bid not found")

    # Fetch listing to verify contractor ownership
    listing_res = await db.execute(select(MarketplaceListing).filter(MarketplaceListing.id == tx.listing_id))
    listing = listing_res.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated listing not found")

    if listing.seller_id != current_user.id and current_user.role not in [UserRole.ADMIN, "ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this bid status")

    if update_in.status:
        try:
            tx.status = TransactionStatus(update_in.status.upper())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid transaction status: {update_in.status}")

    if update_in.notes:
        tx.notes = update_in.notes

    # If accepted, reduce available tonnage or mark listing reserved
    if tx.status == TransactionStatus.ACCEPTED:
        listing.available_tonnes = max(0.0, listing.available_tonnes - tx.requested_tonnes)
        if listing.available_tonnes <= 0:
            listing.status = ListingStatus.SOLD
            listing.sold_at = datetime.now(timezone.utc)
        else:
            listing.status = ListingStatus.RESERVED

    await db.commit()
    await db.refresh(tx)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.APPROVE if tx.status == TransactionStatus.ACCEPTED else AuditAction.UPDATE,
        resource_type="EnquiryTransaction",
        resource_id=tx.id,
        change_details={"new_status": tx.status.value, "requested_tonnes": tx.requested_tonnes},
        request=request,
    )

    return tx
