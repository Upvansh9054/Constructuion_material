import io
import os
import uuid
import pytest
from PIL import Image, ImageDraw
from httpx import AsyncClient

from app.core.constants import MaterialCategory, ConditionGrade
from ai_pipeline.dataset_annotator import MATERIAL_CLASS_NAMES


def create_test_demolition_image(width: int = 640, height: int = 480) -> bytes:
    """
    Creates a synthetic demolition scene image with distinct geometric features
    simulating concrete blocks and steel beams.
    """
    img = Image.new("RGB", (width, height), color=(180, 180, 180))
    draw = ImageDraw.Draw(img)

    # Simulate concrete pile (gray rectangle)
    draw.rectangle([50, 80, 300, 380], fill=(120, 120, 125), outline=(90, 90, 95), width=3)
    # Simulate steel beam (dark blue-gray elongated bar)
    draw.rectangle([340, 100, 420, 420], fill=(70, 80, 95), outline=(40, 50, 65), width=3)
    # Simulate brick rubble (terracotta patches)
    draw.rectangle([450, 200, 600, 350], fill=(160, 60, 45), outline=(130, 40, 30), width=3)

    bio = io.BytesIO()
    img.save(bio, format="JPEG", quality=90)
    return bio.getvalue()


@pytest.mark.asyncio
async def test_models_evaluation_catalog(async_client: AsyncClient, contractor_headers: dict):
    """
    Verify candidate YOLO object detection and instance segmentation models evaluation endpoint:
    Returns empirical benchmarks (yolov8n, yolov8s, yolov8m, yolov8s-seg, yolo11n).
    """
    resp = await async_client.get("/api/v1/analysis/models/evaluation", headers=contractor_headers)
    assert resp.status_code == 200
    models = resp.json()

    assert len(models) >= 5
    model_names = [m["model_name"].lower() for m in models]
    assert "yolov8n" in model_names
    assert "yolov8s" in model_names
    assert "yolov8s-seg" in model_names
    assert "yolo11n" in model_names

    for m in models:
        assert m["parameter_count_millions"] > 0
        assert m["latency_cpu_ms"] > 0
        assert 0.0 < m["mAP50_coco_baseline"] <= 100.0
        assert "demolition_suitability_grade" in m
        assert len(m["evaluation_notes"]) > 10


@pytest.mark.asyncio
async def test_dataset_generation_and_validation(async_client: AsyncClient, contractor_headers: dict):
    """
    Verify dataset validation endpoint and sample synthetic dataset generator for the 6 material classes.
    """
    resp = await async_client.post(
        "/api/v1/analysis/dataset/generate-sample?num_train=6&num_val=2",
        headers=contractor_headers,
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["is_ready_for_training"] is True
    assert data["train_count"] == 6
    assert data["val_count"] == 2
    assert len(data["classes"]) == 6
    classes_lower = [c.lower() for c in data["classes"]]
    for cls_name in ["concrete", "bricks", "steel", "timber", "glass", "mixed_debris"]:
        assert cls_name in classes_lower

    # Also verify GET /dataset/stats
    stats_resp = await async_client.get("/api/v1/analysis/dataset/stats", headers=contractor_headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["train_count"] >= 6
    assert stats["val_count"] >= 2


@pytest.mark.asyncio
async def test_training_pipeline_readiness_check(async_client: AsyncClient, contractor_headers: dict):
    """
    Verify training pipeline honesty: when requested on a non-existent or empty dataset,
    it returns success=False with clear explanatory notes without fabricating metrics.
    """
    req_body = {
        "base_model": "yolov8s.pt",
        "dataset_yaml_path": "ai_pipeline/datasets/non_existent_dataset.yaml",
        "epochs": 10,
        "batch_size": 16,
    }
    resp = await async_client.post("/api/v1/analysis/train", json=req_body, headers=contractor_headers)
    assert resp.status_code == 200
    res = resp.json()

    assert res["success"] is False
    assert "not found" in res["message"].lower() or "missing" in res["message"].lower()
    # Honest engineering: metrics should be None when uncompleted
    assert res["metrics"] is None


@pytest.mark.asyncio
async def test_single_image_inference_file_upload(async_client: AsyncClient, contractor_headers: dict):
    """
    Test synchronous AI material inference via file upload:
    - Identifies materials among 6 classes
    - Returns bounding boxes, confidence, model version, latency
    - Renders visual annotations on the image
    """
    img_bytes = create_test_demolition_image(640, 480)

    files = {"file": ("demolition_site.jpg", img_bytes, "image/jpeg")}
    data = {"confidence_threshold": "0.30", "iou_threshold": "0.45"}

    resp = await async_client.post(
        "/api/v1/analysis/infer-image",
        files=files,
        data=data,
        headers=contractor_headers,
    )
    assert resp.status_code == 200
    result = resp.json()

    assert result["file_name"] == "demolition_site.jpg"
    assert result["image_width"] == 640
    assert result["image_height"] == 480
    assert result["inference_latency_ms"] > 0
    assert "model_version" in result
    assert "model_architecture" in result
    assert result["annotated_download_url"] is not None

    # Check detections
    detections = result["detections"]
    assert len(detections) > 0
    valid_categories = {c.value for c in MaterialCategory}

    for det in detections:
        assert det["category"] in valid_categories
        assert 0.0 <= det["x_min"] <= 1.0
        assert 0.0 <= det["y_min"] <= 1.0
        assert det["x_max"] >= det["x_min"]
        assert det["y_max"] >= det["y_min"]
        assert 0.0 <= det["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_image_id_inference(async_client: AsyncClient, contractor_headers: dict):
    """
    Test synchronous AI material inference using an uploaded SurveyImage ID.
    """
    # 1. Create Site
    site_payload = {
        "site_code": f"SITE-AI-{uuid.uuid4().hex[:6].upper()}",
        "name": "Harbor Warehouse AI Test",
        "address": "404 Wharf St",
        "city": "Liverpool",
        "state": "North West",
        "postal_code": "L3 4FP",
        "country": "United Kingdom",
        "building_type": "Industrial Warehouse",
        "footprint_sqm": 1200.0,
        "building_height_m": 12.0,
        "number_of_floors": 2,
    }
    site_res = await async_client.post("/api/v1/sites/", json=site_payload, headers=contractor_headers)
    assert site_res.status_code == 201
    site_id = site_res.json()["id"]

    # 2. Create Survey
    survey_payload = {
        "site_id": site_id,
        "assessment_name": "AI Vision Benchmark Survey",
        "survey_date": "2026-11-12",
        "weather_condition": "Overcast",
    }
    survey_res = await async_client.post("/api/v1/surveys/", json=survey_payload, headers=contractor_headers)
    assert survey_res.status_code == 201
    survey_id = survey_res.json()["id"]

    # 3. Upload Survey Image
    img_bytes = create_test_demolition_image(640, 480)
    upload_files = [("files", ("survey_wall.jpg", img_bytes, "image/jpeg"))]
    upload_res = await async_client.post(
        f"/api/v1/surveys/{survey_id}/upload-media",
        files=upload_files,
        headers=contractor_headers,
    )
    assert upload_res.status_code == 200
    uploaded_images = upload_res.json()["images"]
    assert len(uploaded_images) >= 1
    image_id = uploaded_images[0]["id"]

    # 4. Call /infer-image with image_id
    infer_resp = await async_client.post(
        "/api/v1/analysis/infer-image",
        data={"image_id": image_id, "confidence_threshold": "0.25"},
        headers=contractor_headers,
    )
    assert infer_resp.status_code == 200
    infer_data = infer_resp.json()
    assert infer_data["image_id"] == image_id
    assert len(infer_data["detections"]) > 0
    assert infer_data["annotated_download_url"] is not None


@pytest.mark.asyncio
async def test_human_in_the_loop_label_correction(async_client: AsyncClient, contractor_headers: dict):
    """
    Test Human-in-the-Loop label correction:
    - Contractor reviews detection and changes category from CONCRETE to STEEL
    - Database MaterialItem is updated with verified status
    - Active learning sample is exported to continuous retraining pool
    """
    # 1. Create Site
    site_payload = {
        "site_code": f"SITE-CORR-{uuid.uuid4().hex[:6].upper()}",
        "name": "Correction Test Facility",
        "address": "10 Steelworks Way",
        "city": "Sheffield",
        "state": "Yorkshire",
        "postal_code": "S1 2AA",
        "country": "United Kingdom",
        "building_type": "Factory",
        "footprint_sqm": 500.0,
        "building_height_m": 8.0,
        "number_of_floors": 1,
    }
    site_res = await async_client.post("/api/v1/sites/", json=site_payload, headers=contractor_headers)
    assert site_res.status_code == 201
    site_id = site_res.json()["id"]

    # 2. Create Survey
    survey_payload = {
        "site_id": site_id,
        "assessment_name": "Label Verification Survey",
        "survey_date": "2026-11-12",
    }
    survey_res = await async_client.post("/api/v1/surveys/", json=survey_payload, headers=contractor_headers)
    assert survey_res.status_code == 201
    survey_id = survey_res.json()["id"]

    # 3. Upload Source Image
    img_bytes = create_test_demolition_image(640, 480)
    upload_res = await async_client.post(
        f"/api/v1/surveys/{survey_id}/upload-media",
        files=[("files", ("source_element.jpg", img_bytes, "image/jpeg"))],
        headers=contractor_headers,
    )
    assert upload_res.status_code == 200
    image_id = upload_res.json()["images"][0]["id"]

    # 4. Create Material Item (initially misclassified as CONCRETE)
    material_payload = {
        "survey_id": survey_id,
        "source_image_id": image_id,
        "category": MaterialCategory.CONCRETE.value,
        "subcategory": "Concrete Column (Misclassified)",
        "condition_grade": ConditionGrade.REUSABLE_GOOD.value,
        "estimated_volume_m3": 3.5,
        "estimated_weight_tonnes": 8.4,
        "confidence_score": 0.62,
        "bounding_box": {"x_min": 0.1, "y_min": 0.1, "x_max": 0.5, "y_max": 0.8},
    }
    mat_res = await async_client.post("/api/v1/materials/", json=material_payload, headers=contractor_headers)
    assert mat_res.status_code == 201
    material_id = mat_res.json()["id"]

    # 5. Call /annotations/correct
    correction_payload = {
        "material_item_id": material_id,
        "corrected_category": MaterialCategory.STEEL.value,
        "corrected_subcategory": "Structural I-Beam Section",
        "condition_grade": ConditionGrade.REUSABLE_EXCELLENT.value,
        "notes": "Verified by Site Engineer: Grade S355 Structural Steel Column",
        "save_to_training_pool": True,
    }

    resp = await async_client.post(
        "/api/v1/analysis/annotations/correct",
        json=correction_payload,
        headers=contractor_headers,
    )
    assert resp.status_code == 200
    corr_data = resp.json()

    assert corr_data["material_item_id"] == material_id
    assert corr_data["previous_category"] == MaterialCategory.CONCRETE.value
    assert corr_data["updated_category"] == MaterialCategory.STEEL.value
    assert corr_data["is_verified"] is True
    assert corr_data["training_sample_saved"] is True
    assert corr_data["training_dataset_path"] is not None

    # 6. Verify GET Material Item
    get_mat_res = await async_client.get(f"/api/v1/materials/{material_id}", headers=contractor_headers)
    assert get_mat_res.status_code == 200
    updated_mat = get_mat_res.json()
    assert updated_mat["category"] == MaterialCategory.STEEL.value
    assert updated_mat["subcategory"] == "Structural I-Beam Section"
    assert updated_mat["condition_grade"] == ConditionGrade.REUSABLE_EXCELLENT.value
    assert updated_mat["is_verified_by_surveyor"] is True
