import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_demolition_and_material_flow(
    async_client: AsyncClient,
    contractor_headers: dict,
    buyer_headers: dict,
):
    # 1. Create a Demolition Site
    site_payload = {
        "site_code": "SITE-DETROIT-001",
        "name": "St. Jude Medical Annex",
        "description": "5-storey healthcare pavilion deconstruction",
        "address": "4500 Woodward Ave",
        "city": "Detroit",
        "state": "MI",
        "postal_code": "48201",
        "country": "USA",
        "footprint_sqm": 6200.0,
        "structural_type": "Reinforced Concrete Frame",
        "has_asbestos_risk": False,
        "has_lead_paint": False,
        "status": "PLANNING",
    }
    site_res = await async_client.post("/api/v1/sites/", json=site_payload, headers=contractor_headers)
    assert site_res.status_code == 201
    site = site_res.json()
    site_id = site["id"]
    assert site["site_code"] == "SITE-DETROIT-001"

    # 2. List sites
    sites_list_res = await async_client.get("/api/v1/sites/", headers=contractor_headers)
    assert sites_list_res.status_code == 200
    assert sites_list_res.json()["total"] >= 1

    # 3. Create a Site Survey
    survey_payload = {
        "site_id": site_id,
        "survey_date": "2026-05-15",
        "weather_condition": "Clear sunlight",
        "survey_notes": "Photogrammetry grid flight at 40m AGL.",
    }
    survey_res = await async_client.post("/api/v1/surveys/", json=survey_payload, headers=contractor_headers)
    assert survey_res.status_code == 201
    survey = survey_res.json()
    survey_id = survey["id"]

    # 4. Log a Recovered Material Item (Structural Steel)
    material_payload = {
        "survey_id": survey_id,
        "category": "STEEL",
        "subcategory": "Universal Heavy I-Beams",
        "description": "Structural S355 grade portal frame beams",
        "condition_grade": "REUSABLE_EXCELLENT",
        "estimated_volume_m3": 12.0,
        "estimated_weight_tonnes": 94.2,
        "packing_factor": 0.85,
        "calculation_method": "calibrated_gsd_photogrammetry",
        "confidence_score": 0.95,
        "bounding_box": {"x_min": 100, "y_min": 150, "x_max": 750, "y_max": 500},
    }
    mat_res = await async_client.post("/api/v1/materials/", json=material_payload, headers=contractor_headers)
    assert mat_res.status_code == 201
    material = mat_res.json()
    material_id = material["id"]
    assert material["category"] == "STEEL"
    assert material["estimated_market_value_usd"] > 0
    assert material["embodied_carbon_offset_kg"] > 0
    assert material["is_verified_by_surveyor"] is False

    # 5. Verify Material Item by Surveyor
    verify_res = await async_client.post(f"/api/v1/materials/{material_id}/verify", headers=contractor_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["is_verified_by_surveyor"] is True

    # 6. Check Valuation Summary
    val_res = await async_client.get(f"/api/v1/materials/summary/{survey_id}", headers=contractor_headers)
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["total_recoverable_tonnes"] == 94.2
    assert len(val_data["categories"]) == 1

    # 7. Create Marketplace Listing for the Steel
    listing_payload = {
        "material_item_id": material_id,
        "title": "94.2 Tonnes High Grade Reusable Universal Beams",
        "description": "Salvaged pristine steel sections ready for collection.",
        "available_tonnes": 94.2,
        "min_order_tonnes": 10.0,
        "price_per_tonne_usd": 410.0,
        "pickup_address": "4500 Woodward Ave, Detroit, MI",
        "pickup_city": "Detroit",
        "logistics_notes": "Loading dock crane available.",
    }
    listing_res = await async_client.post("/api/v1/marketplace/", json=listing_payload, headers=contractor_headers)
    assert listing_res.status_code == 201
    listing = listing_res.json()
    listing_id = listing["id"]
    assert listing["total_price_usd"] == round(94.2 * 410.0, 2)

    # 8. Submit Bid / Purchase Enquiry from Material Buyer
    bid_payload = {
        "listing_id": listing_id,
        "requested_tonnes": 40.0,
        "bid_price_per_tonne_usd": 400.0,
        "haulage_type": "FLATBED_TRAILER",
        "notes": "Ready to pick up on Wednesday with 2 flatbed trailers.",
    }
    bid_res = await async_client.post(f"/api/v1/marketplace/{listing_id}/bids", json=bid_payload, headers=buyer_headers)
    assert bid_res.status_code == 201
    bid = bid_res.json()
    assert bid["total_offer_usd"] == 16000.0
    assert bid["status"] == "PENDING"

