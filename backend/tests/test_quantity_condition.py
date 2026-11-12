import base64
import cv2
import numpy as np
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_assumptions_defaults(async_client: AsyncClient, contractor_headers: dict):
    """Verify CIRIA, Eurocode, and regulatory standard default density and packing assumptions."""
    res = await async_client.get("/api/v1/materials/assumptions/defaults", headers=contractor_headers)
    assert res.status_code == 200
    data = res.json()

    assert "densities" in data
    assert "packing_factors" in data
    assert "depth_priors" in data
    assert "regulatory_guidance" in data

    # Verify all 6 initial material categories are configured
    for cat in ["CONCRETE", "BRICKS", "STEEL", "TIMBER", "GLASS", "MIXED_DEBRIS"]:
        assert cat in data["densities"]
        assert "nominal" in data["densities"][cat]
        assert data["densities"][cat]["min"] <= data["densities"][cat]["nominal"] <= data["densities"][cat]["max"]

        assert cat in data["packing_factors"]
        assert "nominal" in data["packing_factors"][cat]

        assert cat in data["depth_priors"]
        assert "nominal" in data["depth_priors"][cat]

    assert "EPA_NESHAP" in data["regulatory_guidance"]
    assert "OSHA_29_CFR_1926_62" in data["regulatory_guidance"]


@pytest.mark.asyncio
async def test_estimate_quantities_calibrated_gsd(async_client: AsyncClient, contractor_headers: dict):
    """Test photogrammetric volumetric and mass estimation via calibrated camera GSD."""
    payload = {
        "category": "CONCRETE",
        "image_width": 1920,
        "image_height": 1080,
        "camera_height_m": 12.0,
        "focal_length_mm": 24.0,
        "sensor_width_mm": 13.2,
        "detection_box": {"x_min": 0.2, "y_min": 0.2, "x_max": 0.8, "y_max": 0.8},
    }
    res = await async_client.post("/api/v1/materials/estimate-quantities", json=payload, headers=contractor_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["estimation_method"] == "CALIBRATED_MONOCULAR_GSD"
    assert data["uncertainty_percentage"] == 22.0
    assert data["dimension_length_m"] > 0
    assert data["dimension_width_m"] > 0
    assert data["dimension_height_m"] > 0
    assert data["surface_area_m2"] > 0
    assert data["nominal_volume_m3"] > 0
    assert data["nominal_weight_tonnes"] > 0

    # Explicit uncertainty bounds verification [min, nominal, max]
    assert data["min_volume_m3"] <= data["nominal_volume_m3"] <= data["max_volume_m3"]
    assert data["min_weight_tonnes"] <= data["nominal_weight_tonnes"] <= data["max_weight_tonnes"]
    assert data["assumed_density_t_per_m3"] == 2.40


@pytest.mark.asyncio
async def test_estimate_quantities_reference_object(async_client: AsyncClient, contractor_headers: dict):
    """Test dimension scaling via known physical reference object (e.g. 1.0m surveyor rod)."""
    payload = {
        "category": "STEEL",
        "reference_measurement_m": 1.0,
        "reference_pixel_length": 100.0,
        "image_width": 1920,
        "image_height": 1080,
        "detection_box": {"x_min": 0.1, "y_min": 0.1, "x_max": 0.5, "y_max": 0.7},
    }
    res = await async_client.post("/api/v1/materials/estimate-quantities", json=payload, headers=contractor_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["estimation_method"] == "REFERENCE_OBJECT_SCALED"
    assert data["uncertainty_percentage"] == 18.0
    assert data["dimension_width_m"] > 0
    assert data["dimension_length_m"] > 0
    assert data["assumed_density_t_per_m3"] == 7.85
    assert data["packing_factor"] == 0.48


@pytest.mark.asyncio
async def test_estimate_quantities_manual_takeoff(async_client: AsyncClient, contractor_headers: dict):
    """Test surveyor direct physical takeoff measurements."""
    payload = {
        "category": "BRICKS",
        "manual_length_m": 10.0,
        "manual_width_m": 4.5,
        "manual_height_m": 0.60,
        "custom_density_t_per_m3": 1.95,
        "custom_packing_factor": 0.80,
    }
    res = await async_client.post("/api/v1/materials/estimate-quantities", json=payload, headers=contractor_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["estimation_method"] == "MANUAL_SURVEYOR_TAKEOFF"
    assert data["uncertainty_percentage"] == 10.0
    assert data["dimension_length_m"] == 10.0
    assert data["dimension_width_m"] == 4.5
    assert data["dimension_height_m"] == 0.60
    assert data["surface_area_m2"] == 45.0
    assert data["assumed_density_t_per_m3"] == 1.95
    assert data["packing_factor"] == 0.80

    expected_volume = round(45.0 * 0.60 * 0.80, 3)
    assert abs(data["nominal_volume_m3"] - expected_volume) < 0.1


@pytest.mark.asyncio
async def test_assess_condition_structural_defects(async_client: AsyncClient, contractor_headers: dict):
    """Test multi-factor CV defect quantification on synthetic rusted steel patch."""
    # Create synthetic image with orange/brown rust tones
    patch = np.zeros((100, 100, 3), dtype=np.uint8)
    patch[:, :] = (30, 90, 180)  # BGR orange-brown rust color
    _, buf = cv2.imencode(".jpg", patch)
    b64_patch = base64.b64encode(buf.tobytes()).decode("utf-8")

    payload = {
        "category": "STEEL",
        "crop_image_bytes_base64": b64_patch,
    }
    res = await async_client.post("/api/v1/materials/assess-condition", json=payload, headers=contractor_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["damage_severity_pct"] > 0.0
    assert data["damage_type"] is not None
    assert data["recommended_recovery_route"] in ["DIRECT_REUSE", "CLOSED_LOOP_RECYCLING"]
    assert len(data["indicators"]) > 0


@pytest.mark.asyncio
async def test_assess_condition_asbestos_hazard(async_client: AsyncClient, contractor_headers: dict):
    """
    Test mandatory EPA NESHAP asbestos contamination rule:
    Prohibits recycling and forces route to HAZARDOUS_DISPOSAL with 0% recoverability.
    """
    payload = {
        "category": "MIXED_DEBRIS",
        "site_has_asbestos_risk": True,
    }
    res = await async_client.post("/api/v1/materials/assess-condition", json=payload, headers=contractor_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["requires_specialist_abatement"] is True
    assert data["grade"] == "HAZARDOUS_CONTAMINATED"
    assert data["recommended_recovery_route"] == "HAZARDOUS_DISPOSAL"
    assert data["recoverability_percentage"] == 0.0
    assert data["hazard_inspection_warning"] is not None
    assert "EPA" in data["hazard_inspection_warning"]


@pytest.mark.asyncio
async def test_weighbridge_verification_flow(async_client: AsyncClient, contractor_headers: dict):
    """
    Test decoupling of visual pre-demolition estimates and legal certified weighbridge tickets.
    Verifies that initial estimated mass is unmutated while verified mass and variance delta are saved.
    """
    # 1. Create site
    site_res = await async_client.post(
        "/api/v1/sites/",
        json={
            "site_code": "SITE-SCALE-001",
            "name": "Industrial Terminal Demolition",
            "address": "100 Port Rd",
            "city": "Cleveland",
            "state": "OH",
            "postal_code": "44101",
            "country": "USA",
            "footprint_sqm": 4200.0,
            "structural_type": "Steel Mill Structure",
        },
        headers=contractor_headers,
    )
    assert site_res.status_code == 201
    site_id = site_res.json()["id"]

    # 2. Create survey
    survey_res = await async_client.post(
        "/api/v1/surveys/",
        json={
            "site_id": site_id,
            "survey_date": "2026-06-01",
            "survey_notes": "Initial pre-demolition quantity estimation",
        },
        headers=contractor_headers,
    )
    assert survey_res.status_code == 201
    survey_id = survey_res.json()["id"]

    # 3. Create material with visual pre-demolition estimate
    initial_estimated_mass = 75.0
    mat_res = await async_client.post(
        "/api/v1/materials/",
        json={
            "survey_id": survey_id,
            "category": "STEEL",
            "subcategory": "Heavy Wide-Flange Columns",
            "condition_grade": "REUSABLE_EXCELLENT",
            "estimated_volume_m3": 10.0,
            "estimated_weight_tonnes": initial_estimated_mass,
            "uncertainty_percentage": 15.0,
            "calculation_method": "calibrated_gsd_photogrammetry",
        },
        headers=contractor_headers,
    )
    assert mat_res.status_code == 201
    mat_id = mat_res.json()["id"]

    # 4. Verify Weighbridge Ticket measurement (certified scale ticket)
    verified_scale_mass = 72.8
    ticket_no = "WB-2026-CERT-88412"
    scale_id = "SCALE-PORT-02"

    wb_res = await async_client.post(
        f"/api/v1/materials/{mat_id}/verify-weighbridge",
        json={
            "verified_weight_tonnes": verified_scale_mass,
            "weighbridge_ticket_number": ticket_no,
            "weighbridge_scale_id": scale_id,
            "surveyor_notes": "Gross 98.8t tare 26.0t certified at Port Weighbridge.",
        },
        headers=contractor_headers,
    )
    assert wb_res.status_code == 200
    wb_data = wb_res.json()

    # Pre-demolition estimate MUST REMAIN UNMUTATED
    assert wb_data["estimated_weight_tonnes"] == initial_estimated_mass
    assert wb_data["verified_weight_tonnes"] == verified_scale_mass
    assert wb_data["weight_delta_tonnes"] == round(verified_scale_mass - initial_estimated_mass, 3)
    assert wb_data["weighbridge_ticket_number"] == ticket_no
    assert wb_data["is_verified"] is True

    # 5. Fetch material item to confirm both estimates and scale measurements coexist in database
    get_res = await async_client.get(f"/api/v1/materials/{mat_id}", headers=contractor_headers)
    assert get_res.status_code == 200
    mat_record = get_res.json()

    assert mat_record["estimated_weight_tonnes"] == initial_estimated_mass
    assert mat_record["verified_weight_tonnes"] == verified_scale_mass
    assert mat_record["weighbridge_ticket_number"] == ticket_no
    assert mat_record["weighbridge_scale_id"] == scale_id
    assert mat_record["is_verified_by_surveyor"] is True


@pytest.mark.asyncio
async def test_open3d_stereo_pointcloud_reconstruction(async_client: AsyncClient, contractor_headers: dict):
    """Test Open3D stereo point cloud reconstruction endpoint with synthetic stereo pair."""
    # Generate two high-contrast patterned synthetic images with slight horizontal disparity
    img_a = np.zeros((300, 300, 3), dtype=np.uint8)
    img_b = np.zeros((300, 300, 3), dtype=np.uint8)

    for i in range(10, 290, 20):
        for j in range(10, 290, 20):
            cv2.rectangle(img_a, (i, j), (i + 10, j + 10), (255, 255, 255), -1)
            cv2.rectangle(img_b, (i + 2, j), (i + 12, j + 10), (255, 255, 255), -1)

    _, buf_a = cv2.imencode(".png", img_a)
    _, buf_b = cv2.imencode(".png", img_b)

    b64_a = base64.b64encode(buf_a.tobytes()).decode("utf-8")
    b64_b = base64.b64encode(buf_b.tobytes()).decode("utf-8")

    payload = {
        "image_a_base64": b64_a,
        "image_b_base64": b64_b,
        "focal_length_mm": 24.0,
        "sensor_width_mm": 13.2,
        "baseline_distance_m": 1.5,
    }

    res = await async_client.post("/api/v1/materials/reconstruct-3d", json=payload, headers=contractor_headers)
    assert res.status_code == 200
    data = res.json()

    assert "point_count" in data
    assert "bounding_box_3d" in data
    assert "convex_hull_volume_m3" in data
    assert "reconstruction_confidence" in data
    assert "methodology_used" in data

