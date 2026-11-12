import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_user, record_audit_log, require_contractor
from app.core.constants import AuditAction, ConditionGrade, MaterialCategory
from app.core.database import get_db
from app.models.material import MaterialCategoryDefinition, MaterialItem
from app.models.survey import SiteSurvey, SurveyImage
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.material import (
    AssumptionsDefaultsResponse,
    MaterialCategoryDefinitionResponse,
    MaterialCategorySummary,
    MaterialConditionAssessmentRequest,
    MaterialConditionAssessmentResponse,
    MaterialItemCreate,
    MaterialItemResponse,
    MaterialItemUpdate,
    QuantityEstimationRequest,
    QuantityEstimationResponse,
    StereoReconstructionRequest,
    StereoReconstructionResponse,
    ValuationSummary,
    WeighbridgeVerificationRequest,
    WeighbridgeVerificationResponse,
)
from app.services.storage import storage_service
from app.services.valuation import valuation_service
from ai_pipeline.contracts import DetectionBox
from ai_pipeline.condition_assessor import condition_assessor_extended
from ai_pipeline.photogrammetry_3d import (
    MATERIAL_DENSITY_RANGES,
    PACKING_FACTORS_CONFIG,
    STRUCTURAL_DEPTH_PRIORS,
    photogrammetry_engine,
    quantity_estimator_3d,
)

router = APIRouter()


@router.get("/categories", response_model=List[MaterialCategoryDefinitionResponse])
async def list_material_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve standard material categories, densities, carbon factors, and benchmark prices."""
    result = await db.execute(select(MaterialCategoryDefinition).order_by(MaterialCategoryDefinition.name))
    categories = list(result.scalars().all())
    return categories


@router.post("/", response_model=MaterialItemResponse, status_code=status.HTTP_201_CREATED)
async def create_material_item(
    item_in: MaterialItemCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Create a manual material inventory record."""
    survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.id == item_in.survey_id))
    if not survey_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    weight_tonnes = item_in.estimated_weight_tonnes
    if weight_tonnes <= 0.0 and item_in.estimated_volume_m3 > 0.0:
        weight_tonnes = valuation_service.calculate_weight_from_volume(
            item_in.category, item_in.estimated_volume_m3, item_in.packing_factor
        )

    val_usd, carbon_kg = valuation_service.calculate_valuation(
        item_in.category, item_in.condition_grade, weight_tonnes
    )

    bbox_dict = item_in.bounding_box.model_dump() if item_in.bounding_box else None

    item = MaterialItem(
        survey_id=item_in.survey_id,
        source_image_id=item_in.source_image_id,
        category=item_in.category,
        subcategory=item_in.subcategory,
        description=item_in.description,
        condition_grade=item_in.condition_grade,
        estimated_volume_m3=item_in.estimated_volume_m3,
        estimated_weight_tonnes=weight_tonnes,
        dimension_length_m=item_in.dimension_length_m,
        dimension_width_m=item_in.dimension_width_m,
        dimension_height_m=item_in.dimension_height_m,
        surface_area_m2=item_in.surface_area_m2,
        min_volume_m3=item_in.min_volume_m3,
        max_volume_m3=item_in.max_volume_m3,
        min_weight_tonnes=item_in.min_weight_tonnes,
        max_weight_tonnes=item_in.max_weight_tonnes,
        uncertainty_percentage=item_in.uncertainty_percentage,
        assumed_density_t_per_m3=item_in.assumed_density_t_per_m3,
        reference_measurement_notes=item_in.reference_measurement_notes,
        damage_severity_pct=item_in.damage_severity_pct,
        damage_type=item_in.damage_type,
        requires_specialist_abatement=item_in.requires_specialist_abatement,
        hazard_inspection_warning=item_in.hazard_inspection_warning,
        recommended_recovery_route=item_in.recommended_recovery_route,
        recoverability_percentage=item_in.recoverability_percentage,
        unit_count=item_in.unit_count,
        packing_factor=item_in.packing_factor,
        calculation_method=item_in.calculation_method,
        contamination_risk=item_in.contamination_risk,
        confidence_score=item_in.confidence_score or 1.0,
        bounding_box=bbox_dict,
        estimated_market_value_usd=val_usd,
        embodied_carbon_offset_kg=carbon_kg,
        is_verified_by_surveyor=False,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="MaterialItem",
        resource_id=item.id,
        change_details={"category": item.category.value, "tonnes": weight_tonnes, "val_usd": val_usd},
        request=request,
    )

    return item


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


@router.get("/assumptions/defaults", response_model=AssumptionsDefaultsResponse)
async def get_assumptions_defaults(
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve CIRIA, Eurocode, and regulatory standard default material densities,
    void packing factors, and structural depth priors.
    """
    densities = {cat.value: vals for cat, vals in MATERIAL_DENSITY_RANGES.items()}
    packing = {cat.value: vals for cat, vals in PACKING_FACTORS_CONFIG.items()}
    depths = {cat.value: vals for cat, vals in STRUCTURAL_DEPTH_PRIORS.items()}
    regulatory = {
        "CIRIA_133": "Guidance on bulk densities of reclaimed construction materials.",
        "EPA_NESHAP": "Mandatory survey for asbestos-containing materials (ACM). Crushing ACM is strictly prohibited under federal Clean Air Act.",
        "OSHA_29_CFR_1926_62": "Pre-1978 structural steel lead paint test required prior to hot work or oxy-fuel cutting.",
        "EUROCODE_EN_1991_1_1": "Standard bulk unit weight of construction rubble and concrete assemblies.",
    }
    return AssumptionsDefaultsResponse(
        densities=densities,
        packing_factors=packing,
        depth_priors=depths,
        regulatory_guidance=regulatory,
    )


@router.post("/estimate-quantities", response_model=QuantityEstimationResponse)
async def estimate_material_quantities(
    req: QuantityEstimationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Calculate physical 3D dimensions, volumetric bounds, and tonnage estimates
    with explicit uncertainty intervals using calibrated GSD or reference markers.
    """
    box = (
        DetectionBox(
            x_min=req.detection_box.x_min,
            y_min=req.detection_box.y_min,
            x_max=req.detection_box.x_max,
            y_max=req.detection_box.y_max,
            confidence=1.0,
            category=req.category,
        )
        if req.detection_box
        else DetectionBox(
            x_min=0.0,
            y_min=0.0,
            x_max=1.0,
            y_max=1.0,
            confidence=1.0,
            category=req.category,
        )
    )

    image_shape = (req.image_height, req.image_width, 3)

    result = quantity_estimator_3d.estimate_from_detection(
        box=box,
        image_shape=image_shape,
        category=req.category,
        camera_height_m=req.camera_height_m,
        focal_length_mm=req.focal_length_mm,
        sensor_width_mm=req.sensor_width_mm,
        reference_measurement_m=req.reference_measurement_m,
        reference_pixel_length=req.reference_pixel_length,
        manual_length_m=req.manual_length_m,
        manual_width_m=req.manual_width_m,
        manual_height_m=req.manual_height_m,
        custom_density_t_per_m3=req.custom_density_t_per_m3,
        custom_packing_factor=req.custom_packing_factor,
    )

    return QuantityEstimationResponse(
        nominal_volume_m3=result.nominal_volume_m3,
        nominal_weight_tonnes=result.nominal_weight_tonnes,
        min_volume_m3=result.min_volume_m3,
        max_volume_m3=result.max_volume_m3,
        min_weight_tonnes=result.min_weight_tonnes,
        max_weight_tonnes=result.max_weight_tonnes,
        uncertainty_percentage=result.uncertainty_percentage,
        dimension_length_m=result.length_m,
        dimension_width_m=result.width_m,
        dimension_height_m=result.height_m,
        surface_area_m2=result.surface_area_m2,
        assumed_density_t_per_m3=result.assumed_density_t_per_m3,
        packing_factor=result.packing_factor,
        estimation_method=result.estimation_method,
        assumptions_applied=result.assumptions_applied,
    )


@router.post("/assess-condition", response_model=MaterialConditionAssessmentResponse)
async def assess_material_condition(
    req: MaterialConditionAssessmentRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Perform multi-factor condition analysis, damage severity quantification,
    and hazardous contamination detection on material image crops.
    """
    crop_bgr = None
    if req.crop_image_bytes_base64:
        try:
            raw_bytes = base64.b64decode(req.crop_image_bytes_base64)
            nparr = np.frombuffer(raw_bytes, np.uint8)
            crop_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception:
            crop_bgr = None

    if crop_bgr is None:
        # Create standard synthetic patch for non-image baseline assessments
        crop_bgr = np.full((120, 120, 3), 128, dtype=np.uint8)

    assessment = condition_assessor_extended.assess_crop_condition(
        crop_bgr=crop_bgr,
        category=req.category,
        building_year=req.building_year,
        site_has_asbestos_risk=req.site_has_asbestos_risk,
        site_has_lead_paint=req.site_has_lead_paint,
        manual_hazard_flags=req.manual_hazard_flags,
    )

    return MaterialConditionAssessmentResponse(
        grade=assessment.grade,
        damage_severity_pct=assessment.damage_severity_pct,
        damage_type=assessment.damage_type,
        contamination_risk=assessment.contamination_risk,
        requires_specialist_abatement=assessment.requires_specialist_abatement,
        hazard_inspection_warning=assessment.hazard_inspection_warning,
        recommended_recovery_route=assessment.recommended_recovery_route,
        recoverability_percentage=assessment.recoverability_percentage,
        inspection_notes=assessment.inspection_notes,
        confidence=assessment.confidence,
        indicators=assessment.indicators,
    )


@router.post("/reconstruct-3d", response_model=StereoReconstructionResponse)
async def reconstruct_3d_pointcloud(
    req: StereoReconstructionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """
    Stereo / multi-view 3D point cloud reconstruction from two demolition survey views.
    Computes metric dimensions, point clouds, and convex hull volumes via Open3D.
    """
    img_a_bgr = None
    img_b_bgr = None

    if req.image_a_base64 and req.image_b_base64:
        try:
            bytes_a = base64.b64decode(req.image_a_base64)
            bytes_b = base64.b64decode(req.image_b_base64)
            img_a_bgr = cv2.imdecode(np.frombuffer(bytes_a, np.uint8), cv2.IMREAD_COLOR)
            img_b_bgr = cv2.imdecode(np.frombuffer(bytes_b, np.uint8), cv2.IMREAD_COLOR)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid base64 image data: {str(e)}")
    elif req.image_a_id and req.image_b_id:
        img_a_rec = (await db.execute(select(SurveyImage).filter(SurveyImage.id == req.image_a_id))).scalar_one_or_none()
        img_b_rec = (await db.execute(select(SurveyImage).filter(SurveyImage.id == req.image_b_id))).scalar_one_or_none()
        if not img_a_rec or not img_b_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both survey images not found")

        bytes_a = await storage_service.get_file(img_a_rec.original_s3_key)
        bytes_b = await storage_service.get_file(img_b_rec.original_s3_key)
        img_a_bgr = cv2.imdecode(np.frombuffer(bytes_a, np.uint8), cv2.IMREAD_COLOR)
        img_b_bgr = cv2.imdecode(np.frombuffer(bytes_b, np.uint8), cv2.IMREAD_COLOR)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either image_a_id and image_b_id, or image_a_base64 and image_b_base64",
        )

    if img_a_bgr is None or img_b_bgr is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not decode stereo image pair")

    recon = photogrammetry_engine.reconstruct_from_stereo_pair(
        image_a_bgr=img_a_bgr,
        image_b_bgr=img_b_bgr,
        focal_length_mm=req.focal_length_mm,
        sensor_width_mm=req.sensor_width_mm,
        baseline_distance_m=req.baseline_distance_m,
        camera_height_m=req.camera_height_m,
    )

    return StereoReconstructionResponse(
        point_count=recon.point_count,
        bounding_box_3d=recon.bounding_box_3d,
        convex_hull_volume_m3=recon.convex_hull_volume_m3,
        reconstruction_confidence=recon.reconstruction_confidence,
        matched_features_count=recon.matched_features_count,
        triangulation_error_px=recon.triangulation_error_px,
        methodology_used=recon.methodology_used,
        point_cloud_summary=recon.point_cloud_summary,
    )


@router.get("/{material_id}", response_model=MaterialItemResponse)
async def get_material_item(
    material_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed material item record."""
    result = await db.execute(select(MaterialItem).filter(MaterialItem.id == material_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material item not found")
    return item


@router.patch("/{material_id}", response_model=MaterialItemResponse)
async def update_material_item(
    material_id: str,
    update_in: MaterialItemUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Allow surveyor to inspect, adjust quantity/condition, and verify detected item."""
    result = await db.execute(select(MaterialItem).filter(MaterialItem.id == material_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material item not found")

    update_dict = update_in.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(item, field, val)

    # Recalculate valuation if volume, weight, condition or category changed
    if any(k in update_dict for k in ["estimated_volume_m3", "estimated_weight_tonnes", "condition_grade", "category", "packing_factor"]):
        packing = item.packing_factor or 0.85
        if "estimated_weight_tonnes" not in update_dict and item.estimated_volume_m3 > 0:
            item.estimated_weight_tonnes = valuation_service.calculate_weight_from_volume(
                item.category, item.estimated_volume_m3, packing
            )
        val_usd, carbon_kg = valuation_service.calculate_valuation(
            item.category, item.condition_grade, item.estimated_weight_tonnes
        )
        item.estimated_market_value_usd = val_usd
        item.embodied_carbon_offset_kg = carbon_kg

    if update_dict.get("is_verified_by_surveyor") is True:
        item.verified_by_user_id = current_user.id

    await db.commit()
    await db.refresh(item)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="MaterialItem",
        resource_id=item.id,
        change_details=update_dict,
        request=request,
    )

    return item


@router.post("/{material_id}/verify", response_model=MaterialItemResponse)
async def verify_material_item(
    material_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Mark material item as verified by surveyor."""
    result = await db.execute(select(MaterialItem).filter(MaterialItem.id == material_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material item not found")

    item.is_verified_by_surveyor = True
    item.verified_by_user_id = current_user.id

    await db.commit()
    await db.refresh(item)

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.APPROVE,
        resource_type="MaterialItem",
        resource_id=item.id,
        change_details={"verified_by": current_user.email},
        request=request,
    )

    return item


@router.post("/{material_id}/verify-weighbridge", response_model=WeighbridgeVerificationResponse)
async def verify_weighbridge_measurement(
    material_id: str,
    req: WeighbridgeVerificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """
    Record legally binding certified weighbridge scale ticket measurements,
    preserving initial pre-demolition visual estimates and computing variance delta.
    """
    result = await db.execute(select(MaterialItem).filter(MaterialItem.id == material_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material item not found")

    item.verified_weight_tonnes = req.verified_weight_tonnes
    if req.verified_volume_m3 is not None:
        item.verified_volume_m3 = req.verified_volume_m3
    item.weighbridge_ticket_number = req.weighbridge_ticket_number
    item.weighbridge_scale_id = req.weighbridge_scale_id
    item.weighbridge_timestamp = req.weighbridge_timestamp or datetime.now(timezone.utc)
    item.is_verified_by_surveyor = True
    item.verified_by_user_id = current_user.id
    item.verified_at = datetime.now(timezone.utc)

    if req.surveyor_notes:
        existing_notes = item.reference_measurement_notes or ""
        item.reference_measurement_notes = f"{existing_notes}\nWeighbridge verification note: {req.surveyor_notes}".strip()

    await db.commit()
    await db.refresh(item)

    delta_tonnes = round(req.verified_weight_tonnes - item.estimated_weight_tonnes, 3)
    variance_pct = round(
        (delta_tonnes / (item.estimated_weight_tonnes if item.estimated_weight_tonnes > 0 else 1.0)) * 100.0,
        2,
    )

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.APPROVE,
        resource_type="MaterialItem",
        resource_id=item.id,
        change_details={
            "ticket": req.weighbridge_ticket_number,
            "estimated_tonnes": item.estimated_weight_tonnes,
            "verified_tonnes": req.verified_weight_tonnes,
            "delta_tonnes": delta_tonnes,
            "variance_pct": variance_pct,
        },
        request=request,
    )

    return WeighbridgeVerificationResponse(
        material_item_id=item.id,
        estimated_weight_tonnes=item.estimated_weight_tonnes,
        verified_weight_tonnes=req.verified_weight_tonnes,
        weight_delta_tonnes=delta_tonnes,
        weight_variance_percentage=variance_pct,
        weighbridge_ticket_number=req.weighbridge_ticket_number,
        is_verified=item.is_verified_by_surveyor,
        verified_by_user_id=current_user.id,
        verified_at=item.verified_at,
    )


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material_item(
    material_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_contractor),
):
    """Delete a material item record."""
    result = await db.execute(select(MaterialItem).filter(MaterialItem.id == material_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material item not found")

    await record_audit_log(
        db=db,
        user_id=current_user.id,
        action=AuditAction.DELETE,
        resource_type="MaterialItem",
        resource_id=item.id,
        change_details={"category": item.category.value, "tonnes": item.estimated_weight_tonnes},
        request=request,
    )

    await db.delete(item)
    await db.commit()
    return None
