from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user
from app.core.constants import ConditionGrade, MaterialCategory
from app.core.database import get_db
from app.models.material import MaterialItem
from app.models.survey import SiteSurvey
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.material import (
    MaterialCategorySummary,
    MaterialItemResponse,
    MaterialItemUpdate,
    ValuationSummary,
)
from app.services.valuation import valuation_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MaterialItemResponse])
async def list_materials(
    survey_id: Optional[str] = None,
    category: Optional[MaterialCategory] = None,
    condition: Optional[ConditionGrade] = None,
    is_verified: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List detected and logged material items with multi-criteria filtering."""
    query = select(MaterialItem)
    if survey_id:
        query = query.filter(MaterialItem.survey_id == survey_id)
    if category:
        query = query.filter(MaterialItem.category == category)
    if condition:
        query = query.filter(MaterialItem.condition_grade == condition)
    if is_verified is not None:
        query = query.filter(MaterialItem.is_verified_by_surveyor == is_verified)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(MaterialItem.created_at.desc()).offset(offset).limit(page_size)
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


@router.get("/summary/{survey_id}", response_model=ValuationSummary)
async def get_survey_valuation_summary(
    survey_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregate volume, weight, financial recovery value, and carbon offset by material category."""
    items_result = await db.execute(select(MaterialItem).filter(MaterialItem.survey_id == survey_id))
    items = list(items_result.scalars().all())

    cat_map = {}
    for it in items:
        cat = it.category
        if cat not in cat_map:
            cat_map[cat] = {
                "category": cat,
                "total_volume_m3": 0.0,
                "total_weight_tonnes": 0.0,
                "estimated_value_usd": 0.0,
                "carbon_offset_kg_co2e": 0.0,
                "item_count": 0,
            }
        cat_map[cat]["total_volume_m3"] += it.estimated_volume_m3
        cat_map[cat]["total_weight_tonnes"] += it.estimated_weight_tonnes
        cat_map[cat]["estimated_value_usd"] += it.estimated_market_value_usd
        cat_map[cat]["carbon_offset_kg_co2e"] += it.embodied_carbon_offset_kg
        cat_map[cat]["item_count"] += 1

    categories_list = [
        MaterialCategorySummary(
            category=v["category"],
            total_volume_m3=round(v["total_volume_m3"], 2),
            total_weight_tonnes=round(v["total_weight_tonnes"], 2),
            estimated_value_usd=round(v["estimated_value_usd"], 2),
            carbon_offset_kg_co2e=round(v["carbon_offset_kg_co2e"], 2),
            item_count=v["item_count"],
        )
        for v in cat_map.values()
    ]

    total_val = sum(c.estimated_value_usd for c in categories_list)
    total_tonnes = sum(c.total_weight_tonnes for c in categories_list)
    total_carbon = sum(c.carbon_offset_kg_co2e for c in categories_list)

    return ValuationSummary(
        total_estimated_value_usd=round(total_val, 2),
        total_recoverable_tonnes=round(total_tonnes, 2),
        total_carbon_offset_kg_co2e=round(total_carbon, 2),
        categories=categories_list,
    )


@router.patch("/{material_id}", response_model=MaterialItemResponse)
async def update_material_item(
    material_id: str,
    update_in: MaterialItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Allow surveyor to inspect, adjust quantity/condition, and verify detected item."""
    result = await db.execute(select(MaterialItem).filter(MaterialItem.id == material_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material item not found")

    update_dict = update_in.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(item, field, val)

    # Recalculate valuation if volume, weight, or condition changed
    if any(k in update_dict for k in ["estimated_volume_m3", "estimated_weight_tonnes", "condition_grade", "category"]):
        if "estimated_weight_tonnes" not in update_dict and item.estimated_volume_m3 > 0:
            item.estimated_weight_tonnes = valuation_service.calculate_weight_from_volume(
                item.category, item.estimated_volume_m3
            )
        val_usd, carbon_kg = valuation_service.calculate_valuation(
            item.category, item.condition_grade, item.estimated_weight_tonnes
        )
        item.estimated_market_value_usd = val_usd
        item.embodied_carbon_offset_kg = carbon_kg

    await db.commit()
    await db.refresh(item)
    return item
