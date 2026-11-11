"""Database Seeder for Demolition Intelligence & Material Recovery Platform.

Populates initial production schema across all 15 modules with:
- 5 Standard Users (Admin, Demolition Contractor, Surveyor, Material Buyer, Recycler)
- 6 Standard Material Category Definitions with engineering density & ICE carbon factors
- 2 Demolition Sites with structural and hazardous metadata
- Site Surveys with drone photogrammetry calibrated camera parameters
- Recoverable Material Items (Concrete, Bricks, Steel, Timber, Glass, Mixed Debris)
- Buyer & Recycler Profiles
- Marketplace Listings & Bids
- Demolition Pre-Demolition Audit Report (DMAR)
- Audit Logs
"""
import asyncio
from datetime import date, datetime, timezone
import logging
import sys
import os

# Put backend root on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.core.constants import (
    AuditAction,
    BuyerCompanyType,
    ConditionGrade,
    ListingStatus,
    MaterialCategory,
    MediaType,
    SiteStatus,
    SurveyStatus,
    TransactionStatus,
    UserRole,
)
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.audit_log import AuditLog
from app.models.audit_report import DemolitionAuditReport
from app.models.buyer import BuyerRecyclerProfile
from app.models.marketplace import EnquiryTransaction, MarketplaceListing
from app.models.material import MaterialCategoryDefinition, MaterialItem
from app.models.site import DemolitionSite
from app.models.survey import SiteSurvey, SurveyImage
from app.models.user import User
from app.services.valuation import valuation_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_db")


async def seed():
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Schema verification completed.")

    async with AsyncSessionLocal() as db:
        # 1. Seed Material Categories
        categories_data = [
            {
                "category": MaterialCategory.CONCRETE,
                "name": "Crushed & Structural Concrete",
                "description": "High-grade structural concrete elements and clean crushed aggregates suitable for Type 1 subbase.",
                "standard_density_t_per_m3": 2.40,
                "carbon_offset_factor_kg_per_t": 220.0,
                "default_price_per_t_usd": 28.0,
            },
            {
                "category": MaterialCategory.BRICKS,
                "name": "Reclaimed Facing & Engineering Bricks",
                "description": "Palletized heritage and engineering bricks with lime mortar for architectural reuse.",
                "standard_density_t_per_m3": 1.90,
                "carbon_offset_factor_kg_per_t": 350.0,
                "default_price_per_t_usd": 65.0,
            },
            {
                "category": MaterialCategory.STEEL,
                "name": "Structural Heavy & Scrap Steel",
                "description": "Universal columns, beams, rebar, and light melting scrap for direct remelting or reuse.",
                "standard_density_t_per_m3": 7.85,
                "carbon_offset_factor_kg_per_t": 1800.0,
                "default_price_per_t_usd": 380.0,
            },
            {
                "category": MaterialCategory.TIMBER,
                "name": "Dimensional & Heavy Structural Timber",
                "description": "Heartwood beams, roof joists, floorboards, and clean untreated construction lumber.",
                "standard_density_t_per_m3": 0.65,
                "carbon_offset_factor_kg_per_t": 720.0,
                "default_price_per_t_usd": 120.0,
            },
            {
                "category": MaterialCategory.GLASS,
                "name": "Architectural Float & Glazing Glass",
                "description": "Double-glazed window panels, curtain-wall panes, and clear float cullet for bottle/fiberglass manufacturing.",
                "standard_density_t_per_m3": 2.50,
                "carbon_offset_factor_kg_per_t": 550.0,
                "default_price_per_t_usd": 45.0,
            },
            {
                "category": MaterialCategory.MIXED_DEBRIS,
                "name": "Segregated Mineral Demolition Rubble",
                "description": "Mixed inert rubble comprising mortar, screed, and ceramics for road fill and engineered landscaping.",
                "standard_density_t_per_m3": 1.60,
                "carbon_offset_factor_kg_per_t": 95.0,
                "default_price_per_t_usd": 14.0,
            },
        ]

        for cat in categories_data:
            existing_cat = await db.execute(
                select(MaterialCategoryDefinition).filter(
                    MaterialCategoryDefinition.category == cat["category"]
                )
            )
            if not existing_cat.scalar_one_or_none():
                db.add(MaterialCategoryDefinition(**cat))
        await db.commit()
        logger.info("Material categories seeded.")

        # 2. Seed Standard Users
        users_data = [
            {
                "email": "admin@demolition-intel.com",
                "password": "Admin@Demolition2026!",
                "full_name": "Dr. Elena Vance",
                "role": UserRole.ADMIN,
                "company_name": "Circular Demolition Intelligence HQ",
                "phone_number": "+1 (555) 019-2831",
                "is_superuser": True,
            },
            {
                "email": "contractor@apex-demolition.com",
                "password": "Contractor@2026!",
                "full_name": "Marcus Thorne",
                "role": UserRole.DEMOLITION_CONTRACTOR,
                "company_name": "Apex Deconstruction Ltd.",
                "phone_number": "+1 (555) 014-9922",
                "is_superuser": False,
            },
            {
                "email": "surveyor@apex-demolition.com",
                "password": "Surveyor@2026!",
                "full_name": "Sarah Jenkins",
                "role": UserRole.SURVEYOR,
                "company_name": "Apex Deconstruction Ltd.",
                "phone_number": "+1 (555) 014-9925",
                "is_superuser": False,
            },
            {
                "email": "buyer@metro-steels.com",
                "password": "Buyer@2026!",
                "full_name": "Arthur Pendelton",
                "role": UserRole.MATERIAL_BUYER,
                "company_name": "Metro Structural Steelworks",
                "phone_number": "+1 (555) 018-7711",
                "is_superuser": False,
            },
            {
                "email": "recycler@ecocrete.org",
                "password": "Recycler@2026!",
                "full_name": "Carlos Mendoza",
                "role": UserRole.RECYCLER,
                "company_name": "EcoCrete Aggregate Recovery",
                "phone_number": "+1 (555) 012-3344",
                "is_superuser": False,
            },
        ]

        user_map = {}
        for u in users_data:
            existing = await db.execute(select(User).filter(User.email == u["email"]))
            user = existing.scalar_one_or_none()
            if not user:
                user = User(
                    email=u["email"],
                    hashed_password=get_password_hash(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    company_name=u["company_name"],
                    phone_number=u["phone_number"],
                    is_superuser=u["is_superuser"],
                    is_active=True,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            user_map[u["role"]] = user
        logger.info("Standard users seeded.")

        # 3. Seed Demolition Sites
        contractor = user_map[UserRole.DEMOLITION_CONTRACTOR]
        site_1_res = await db.execute(select(DemolitionSite).filter(DemolitionSite.site_code == "SITE-2026-081"))
        site_1 = site_1_res.scalar_one_or_none()
        if not site_1:
            site_1 = DemolitionSite(
                site_code="SITE-2026-081",
                name="St. Jude Hospital East Wing",
                description="Healthcare facility deconstruction and structural salvage.",
                address="4500 Woodward Avenue",
                city="Detroit",
                state="MI",
                postal_code="48201",
                country="USA",
                latitude=42.3551,
                longitude=-83.0614,
                contractor_id=contractor.id,
                estimated_demolition_date=date(2026, 8, 15),
                status=SiteStatus.PRE_DEMOLITION_SURVEY,
                footprint_sqm=8400.0,
                structural_type="Reinforced Concrete Frame",
                has_asbestos_risk=False,
                has_lead_paint=False,
                hazard_notes="Asbestos abatement completed March 2026. Clean clearance certificate granted.",
            )
            db.add(site_1)
            await db.commit()
            await db.refresh(site_1)

        site_2_res = await db.execute(select(DemolitionSite).filter(DemolitionSite.site_code == "SITE-2026-094"))
        site_2 = site_2_res.scalar_one_or_none()
        if not site_2:
            site_2 = DemolitionSite(
                site_code="SITE-2026-094",
                name="Riverside Industrial Silos & Mill",
                description="Heavy industrial plant dismantling.",
                address="1820 Merwin Avenue",
                city="Cleveland",
                state="OH",
                postal_code="44113",
                country="USA",
                latitude=41.4925,
                longitude=-81.6983,
                contractor_id=contractor.id,
                estimated_demolition_date=date(2026, 10, 30),
                status=SiteStatus.PLANNING,
                footprint_sqm=14200.0,
                structural_type="Heavy Structural Steel & Cast Concrete",
                has_asbestos_risk=False,
                has_lead_paint=False,
                hazard_notes="No active lead paint found on primary gantry cranes.",
            )
            db.add(site_2)
            await db.commit()
            await db.refresh(site_2)
        logger.info("Demolition sites seeded.")

        # 4. Seed Survey & Photogrammetry Camera Media
        surveyor = user_map[UserRole.SURVEYOR]
        survey_res = await db.execute(select(SiteSurvey).filter(SiteSurvey.site_id == site_1.id))
        survey = survey_res.scalar_one_or_none()
        if not survey:
            survey = SiteSurvey(
                site_id=site_1.id,
                surveyor_id=surveyor.id,
                survey_date=date(2026, 4, 12),
                weather_condition="Clear Sunlight, 18C, Wind 4 knots",
                survey_notes="Drone grid photogrammetry flight completed at 45m AGL with 75% forward and side overlap.",
                status=SurveyStatus.ANALYSIS_COMPLETED,
                total_images_count=2,
            )
            db.add(survey)
            await db.commit()
            await db.refresh(survey)

            # Add Survey Images
            img_1 = SurveyImage(
                survey_id=survey.id,
                file_name="DJI_EAST_WING_ORTHO_001.JPG",
                media_type=MediaType.IMAGE,
                original_s3_key=f"raw_surveys/{survey.id}/DJI_EAST_WING_ORTHO_001.JPG",
                file_size_bytes=8420000,
                mime_type="image/jpeg",
                width=4000,
                height=3000,
                camera_altitude_m=45.0,
                focal_length_mm=24.0,
                sensor_width_mm=13.2,
                gsd_cm_per_px=0.62,
                gps_latitude=42.35515,
                gps_longitude=-83.06138,
            )
            img_2 = SurveyImage(
                survey_id=survey.id,
                file_name="DJI_STRUCTURAL_STEEL_PAN_002.JPG",
                media_type=MediaType.IMAGE,
                original_s3_key=f"raw_surveys/{survey.id}/DJI_STRUCTURAL_STEEL_PAN_002.JPG",
                file_size_bytes=9150000,
                mime_type="image/jpeg",
                width=4000,
                height=3000,
                camera_altitude_m=30.0,
                focal_length_mm=24.0,
                sensor_width_mm=13.2,
                gsd_cm_per_px=0.41,
                gps_latitude=42.35520,
                gps_longitude=-83.06145,
            )
            db.add_all([img_1, img_2])
            await db.commit()
            await db.refresh(img_1)
        logger.info("Surveys and calibrated photogrammetry media seeded.")

        # 5. Seed Material Items
        mat_res = await db.execute(select(MaterialItem).filter(MaterialItem.survey_id == survey.id))
        materials = list(mat_res.scalars().all())
        if not materials:
            sample_items = [
                {
                    "survey_id": survey.id,
                    "category": MaterialCategory.STEEL,
                    "subcategory": "Universal Heavy Beams & Columns",
                    "description": "Structural Grade S355 steel I-sections from central portal frames.",
                    "condition_grade": ConditionGrade.REUSABLE_EXCELLENT,
                    "estimated_volume_m3": 18.5,
                    "estimated_weight_tonnes": 120.0,
                    "packing_factor": 0.85,
                    "calculation_method": "calibrated_gsd_photogrammetry",
                    "confidence_score": 0.94,
                    "bounding_box": {"x_min": 120.0, "y_min": 85.0, "x_max": 840.0, "y_max": 650.0},
                    "estimated_market_value_usd": round(120.0 * 380.0 * 1.25, 2),
                    "embodied_carbon_offset_kg": round(120.0 * 1800.0, 2),
                    "is_verified_by_surveyor": True,
                    "surveyor_adjustment_notes": "Ultrasonic thickness measurement confirms zero corrosion loss.",
                    "verified_by_user_id": surveyor.id,
                },
                {
                    "survey_id": survey.id,
                    "category": MaterialCategory.CONCRETE,
                    "subcategory": "Crushed C30/37 Aggregate",
                    "description": "Reinforced foundation pad and floor slabs clean of heavy bitumen.",
                    "condition_grade": ConditionGrade.RECYCLABLE,
                    "estimated_volume_m3": 480.0,
                    "estimated_weight_tonnes": 950.0,
                    "packing_factor": 0.85,
                    "calculation_method": "point_cloud_mesh_integration",
                    "confidence_score": 0.91,
                    "bounding_box": {"x_min": 50.0, "y_min": 300.0, "x_max": 950.0, "y_max": 890.0},
                    "estimated_market_value_usd": round(950.0 * 28.0 * 1.0, 2),
                    "embodied_carbon_offset_kg": round(950.0 * 220.0, 2),
                    "is_verified_by_surveyor": True,
                    "surveyor_adjustment_notes": "Ready for on-site jaw crushing to 40mm down.",
                    "verified_by_user_id": surveyor.id,
                },
                {
                    "survey_id": survey.id,
                    "category": MaterialCategory.BRICKS,
                    "subcategory": "Reclaimed Red Facing Bricks",
                    "description": "Clean clay facing bricks laid with soft lime mortar, easily hand-picked.",
                    "condition_grade": ConditionGrade.REUSABLE_GOOD,
                    "estimated_volume_m3": 45.0,
                    "estimated_weight_tonnes": 78.0,
                    "unit_count": 32000,
                    "packing_factor": 0.90,
                    "calculation_method": "object_count_heuristic",
                    "confidence_score": 0.88,
                    "bounding_box": {"x_min": 250.0, "y_min": 150.0, "x_max": 650.0, "y_max": 520.0},
                    "estimated_market_value_usd": round(78.0 * 65.0 * 1.25, 2),
                    "embodied_carbon_offset_kg": round(78.0 * 350.0, 2),
                    "is_verified_by_surveyor": True,
                    "verified_by_user_id": surveyor.id,
                },
                {
                    "survey_id": survey.id,
                    "category": MaterialCategory.TIMBER,
                    "subcategory": "Old Growth Douglas Fir Trusses",
                    "description": "Massive roof beams and purlins, seasoned and free from fungal rot.",
                    "condition_grade": ConditionGrade.REUSABLE_GOOD,
                    "estimated_volume_m3": 25.0,
                    "estimated_weight_tonnes": 16.25,
                    "packing_factor": 0.85,
                    "calculation_method": "bounding_box_dimension_calc",
                    "confidence_score": 0.86,
                    "estimated_market_value_usd": round(16.25 * 120.0 * 1.25, 2),
                    "embodied_carbon_offset_kg": round(16.25 * 720.0, 2),
                    "is_verified_by_surveyor": True,
                    "verified_by_user_id": surveyor.id,
                },
                {
                    "survey_id": survey.id,
                    "category": MaterialCategory.GLASS,
                    "subcategory": "Commercial Clear Float Curtain Panels",
                    "description": "Double glazed architectural vision lites, intact perimeter seals.",
                    "condition_grade": ConditionGrade.RECYCLABLE,
                    "estimated_volume_m3": 6.5,
                    "estimated_weight_tonnes": 16.0,
                    "packing_factor": 0.95,
                    "calculation_method": "calibrated_gsd_photogrammetry",
                    "confidence_score": 0.82,
                    "estimated_market_value_usd": round(16.0 * 45.0 * 1.0, 2),
                    "embodied_carbon_offset_kg": round(16.0 * 550.0, 2),
                    "is_verified_by_surveyor": False,
                },
                {
                    "survey_id": survey.id,
                    "category": MaterialCategory.MIXED_DEBRIS,
                    "subcategory": "Inert Masonry Backfill",
                    "description": "Plaster, non-structural tile, and screed suitable for clean fill.",
                    "condition_grade": ConditionGrade.DOWN_CYCLE_ONLY,
                    "estimated_volume_m3": 85.0,
                    "estimated_weight_tonnes": 136.0,
                    "packing_factor": 0.80,
                    "calculation_method": "volumetric_elevation_model",
                    "confidence_score": 0.79,
                    "estimated_market_value_usd": round(136.0 * 14.0 * 0.40, 2),
                    "embodied_carbon_offset_kg": round(136.0 * 95.0, 2),
                    "is_verified_by_surveyor": False,
                },
            ]
            for it in sample_items:
                m_item = MaterialItem(**it)
                db.add(m_item)
            await db.commit()
            mat_res = await db.execute(select(MaterialItem).filter(MaterialItem.survey_id == survey.id))
            materials = list(mat_res.scalars().all())
        logger.info("Material items seeded.")

        # 6. Seed Buyer & Recycler Profiles
        buyer_user = user_map[UserRole.MATERIAL_BUYER]
        buyer_profile_res = await db.execute(
            select(BuyerRecyclerProfile).filter(BuyerRecyclerProfile.user_id == buyer_user.id)
        )
        if not buyer_profile_res.scalar_one_or_none():
            b_prof = BuyerRecyclerProfile(
                user_id=buyer_user.id,
                company_name="Metro Structural Steelworks",
                company_type=BuyerCompanyType.STEEL_MILL,
                city="Cleveland",
                state="OH",
                distance_km=28.5,
                accepted_categories=["STEEL", "CONCRETE"],
                certified_standards=["ISO 14001:2015", "LEED Certified Handler", "AISC Quality Fabricator"],
                contact_person="Arthur Pendelton",
                contact_email="buyer@metro-steels.com",
                contact_phone="+1 (555) 018-7711",
                total_purchased_tonnes=1850.0,
                active_bids_count=2,
                rating=4.9,
            )
            db.add(b_prof)

        recycler_user = user_map[UserRole.RECYCLER]
        rec_profile_res = await db.execute(
            select(BuyerRecyclerProfile).filter(BuyerRecyclerProfile.user_id == recycler_user.id)
        )
        if not rec_profile_res.scalar_one_or_none():
            r_prof = BuyerRecyclerProfile(
                user_id=recycler_user.id,
                company_name="EcoCrete Aggregate Recovery",
                company_type=BuyerCompanyType.AGGREGATE_CRUSHER,
                city="Detroit",
                state="MI",
                distance_km=14.2,
                accepted_categories=["CONCRETE", "BRICKS", "MIXED_DEBRIS"],
                certified_standards=["ASTM C33 Recycled Concrete", "Michigan DEQ Permit #4402"],
                contact_person="Carlos Mendoza",
                contact_email="recycler@ecocrete.org",
                contact_phone="+1 (555) 012-3344",
                total_purchased_tonnes=8400.0,
                active_bids_count=1,
                rating=4.8,
            )
            db.add(r_prof)
        await db.commit()
        logger.info("Buyer and recycler directory seeded.")

        # 7. Seed Marketplace Listings and Bids
        steel_item = next((m for m in materials if m.category == MaterialCategory.STEEL), None)
        brick_item = next((m for m in materials if m.category == MaterialCategory.BRICKS), None)

        if steel_item:
            listing_1_res = await db.execute(
                select(MarketplaceListing).filter(MarketplaceListing.material_item_id == steel_item.id)
            )
            listing_1 = listing_1_res.scalar_one_or_none()
            if not listing_1:
                listing_1 = MarketplaceListing(
                    material_item_id=steel_item.id,
                    seller_id=contractor.id,
                    title="120 Tonnes Heavy Structural S355 Universal Beams",
                    description="Pristine structural I-sections salvaged from hospital wing framework. Zero torque distortion.",
                    available_tonnes=120.0,
                    min_order_tonnes=10.0,
                    price_per_tonne_usd=395.0,
                    total_price_usd=47400.0,
                    pickup_address="4500 Woodward Avenue, Gate 3",
                    pickup_city="Detroit",
                    logistics_notes="Site equipped with 50-ton mobile crane. High-boy flatbeds can back directly onto loading bay.",
                    status=ListingStatus.ACTIVE,
                    listed_at=datetime.now(timezone.utc),
                )
                db.add(listing_1)
                await db.commit()
                await db.refresh(listing_1)

                # Add Bid on this listing
                bid = EnquiryTransaction(
                    listing_id=listing_1.id,
                    buyer_id=buyer_user.id,
                    requested_tonnes=60.0,
                    bid_price_per_tonne_usd=390.0,
                    total_offer_usd=23400.0,
                    haulage_type="FLATBED_TRAILER",
                    status=TransactionStatus.PENDING,
                    notes="Can arrange 3 dedicated tandem trailers for immediate collection starting Monday.",
                )
                db.add(bid)
                await db.commit()

        if brick_item:
            listing_2_res = await db.execute(
                select(MarketplaceListing).filter(MarketplaceListing.material_item_id == brick_item.id)
            )
            if not listing_2_res.scalar_one_or_none():
                listing_2 = MarketplaceListing(
                    material_item_id=brick_item.id,
                    seller_id=contractor.id,
                    title="32,000 Heritage Red Facing Bricks (Palletized)",
                    description="Historic early 20th century clay bricks gently cleaned of lime mortar and shrink-wrapped on standard EUR pallets.",
                    available_tonnes=78.0,
                    min_order_tonnes=5.0,
                    price_per_tonne_usd=85.0,
                    total_price_usd=6630.0,
                    pickup_address="4500 Woodward Avenue, Yard A",
                    pickup_city="Detroit",
                    logistics_notes="Forklift loading available on-site.",
                    status=ListingStatus.ACTIVE,
                    listed_at=datetime.now(timezone.utc),
                )
                db.add(listing_2)
                await db.commit()
        logger.info("Marketplace listings and enquiry transactions seeded.")

        # 8. Seed Pre-Demolition Audit Report (DMAR)
        dmar_res = await db.execute(
            select(DemolitionAuditReport).filter(DemolitionAuditReport.survey_id == survey.id)
        )
        if not dmar_res.scalar_one_or_none():
            total_tonnes = sum(m.estimated_weight_tonnes for m in materials)
            total_value = sum(m.estimated_market_value_usd for m in materials)
            total_carbon = sum(m.embodied_carbon_offset_kg for m in materials)

            report = DemolitionAuditReport(
                site_id=site_1.id,
                survey_id=survey.id,
                report_title="Comprehensive Pre-Demolition Material Audit Report (DMAR) - St. Jude East Wing",
                executive_summary=(
                    "Comprehensive Pre-Demolition Audit and photogrammetric inventory completed for St. Jude Hospital East Wing. "
                    "Identified 6 principal material streams totaling 1,316.2 tonnes. Gross estimated circular salvage recovery "
                    "valuation stands at $113,875. Diverting these lots prevents approximately 465 metric tons of CO2e."
                ),
                regulatory_compliance_notes=(
                    "Clean audit. Asbestos abatement cleared. BREEAM Demolition Protocol Compliant. "
                    "Waste diversion target > 85% by weight achievable with current contractor salvage plan."
                ),
                buyer_matching_insights=(
                    "High interest from Metro Structural Steelworks and EcoCrete Aggregates. Logistics routes within 30km radius."
                ),
                total_recoverable_tonnes=round(total_tonnes, 2),
                total_estimated_value_usd=round(total_value, 2),
                total_carbon_offset_kg_co2e=round(total_carbon, 2),
                detailed_breakdown_json={
                    "STEEL": {"tonnes": 120.0, "value_usd": 57000.0, "carbon_kg": 216000.0},
                    "CONCRETE": {"tonnes": 950.0, "value_usd": 26600.0, "carbon_kg": 209000.0},
                    "BRICKS": {"tonnes": 78.0, "value_usd": 6337.5, "carbon_kg": 27300.0},
                    "TIMBER": {"tonnes": 16.25, "value_usd": 2437.5, "carbon_kg": 11700.0},
                    "GLASS": {"tonnes": 16.0, "value_usd": 720.0, "carbon_kg": 8800.0},
                    "MIXED_DEBRIS": {"tonnes": 136.0, "value_usd": 761.6, "carbon_kg": 12920.0},
                },
            )
            db.add(report)
            await db.commit()
        logger.info("Pre-demolition audit report seeded.")

        # 9. Seed Audit Logs
        log_res = await db.execute(select(AuditLog))
        if not log_res.scalars().first():
            logs = [
                AuditLog(
                    user_id=contractor.id,
                    action=AuditAction.CREATE,
                    resource_type="DemolitionSite",
                    resource_id=site_1.id,
                    change_details={"site_code": site_1.site_code, "name": site_1.name},
                    ip_address="192.168.1.100",
                    user_agent="DemolitionIntel/1.0",
                ),
                AuditLog(
                    user_id=surveyor.id,
                    action=AuditAction.APPROVE,
                    resource_type="MaterialItem",
                    resource_id=steel_item.id if steel_item else None,
                    change_details={"verified": True, "category": "STEEL", "tonnes": 120.0},
                    ip_address="192.168.1.102",
                    user_agent="DemolitionIntel/1.0",
                ),
            ]
            db.add_all(logs)
            await db.commit()
        logger.info("Audit logs seeded.")

    logger.info("🎉 Database seeding completed successfully across all 15 modules!")


if __name__ == "__main__":
    asyncio.run(seed())
