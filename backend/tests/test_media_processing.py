import io
import os
import tempfile
import pytest
import cv2
import numpy as np
from PIL import Image
from httpx import AsyncClient
from sqlalchemy import select

from app.core.constants import MediaType, UserRole
from app.core.security import create_access_token
from app.models.site import DemolitionSite
from app.models.survey import SiteSurvey, SurveyImage
from app.models.user import User
from app.services.media_processor import (
    MediaProcessorService,
    media_processor,
)


def create_synthetic_jpeg(width: int = 640, height: int = 480, color=(120, 180, 220)) -> bytes:
    """Helper to generate a valid JPEG image in memory."""
    img = Image.new("RGB", (width, height), color=color)
    bio = io.BytesIO()
    img.save(bio, format="JPEG", quality=90)
    return bio.getvalue()


def create_synthetic_mp4(width: int = 320, height: int = 240, fps: int = 10, num_frames: int = 20) -> str:
    """Helper to generate a small valid MP4 video on disk."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp_path = tmp.name
    tmp.close()

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(tmp_path, fourcc, float(fps), (width, height))

    for i in range(num_frames):
        # First 10 frames dark gray, next 10 frames bright green
        color = (50, 50, 50) if i < 10 else (0, 200, 50)
        frame = np.full((height, width, 3), color, dtype=np.uint8)
        out.write(frame)

    out.release()
    return tmp_path


def test_image_metadata_extraction_and_derivatives():
    """Verify image metadata decoding, thumbnailing, and CV preprocessing."""
    jpeg_bytes = create_synthetic_jpeg(width=800, height=600)
    meta = media_processor.extract_image_metadata(jpeg_bytes)

    assert meta.is_valid is True
    assert meta.width == 800
    assert meta.height == 600

    thumb_bytes, cv_bytes, w, h = media_processor.generate_image_derivatives(jpeg_bytes)
    assert len(thumb_bytes) > 0
    assert len(cv_bytes) > 0

    # Verify thumbnail size <= 320
    thumb_img = Image.open(io.BytesIO(thumb_bytes))
    assert max(thumb_img.size) <= 320


def test_corrupt_and_oversized_image_rejection():
    """Verify corrupt bytes and oversized payloads are cleanly rejected."""
    corrupt_bytes = b"NOT_A_VALID_JPEG_HEADER_12345"
    meta = media_processor.extract_image_metadata(corrupt_bytes)
    assert meta.is_valid is False
    assert "Corrupt or unsupported" in meta.error_message

    oversized_bytes = b"0" * (51 * 1024 * 1024)
    meta_large = media_processor.extract_image_metadata(oversized_bytes)
    assert meta_large.is_valid is False
    assert "exceeds limit" in meta_large.error_message


def test_video_validation_and_deduplication():
    """Verify video inspection and frame deduplication (MAD filtering)."""
    vid_path = create_synthetic_mp4(width=320, height=240, fps=10, num_frames=20)
    try:
        val = media_processor.validate_video_file(vid_path)
        assert val.is_valid is True
        assert val.width == 320
        assert val.height == 240
        assert val.duration_seconds == 2.0
        assert val.fps == 10.0

        # Frame extraction with deduplication:
        # Since first 10 frames are identical and last 10 are identical,
        # deduplication should yield around 2 unique keyframes instead of many duplicate ones
        frames = media_processor.extract_video_frames(
            vid_path,
            interval_seconds=0.5,
            similarity_threshold=0.95,
        )
        assert len(frames) >= 1
        assert len(frames) <= 4  # Duplicate frames were pruned!

    finally:
        if os.path.exists(vid_path):
            os.remove(vid_path)


@pytest.mark.asyncio
async def test_full_site_assessment_and_media_upload_flow(async_client: AsyncClient, contractor_headers: dict):
    """
    End-to-end integration test:
    1. Create site with building dimensions and typology
    2. Create survey assessment session
    3. Upload multiple site images and a video
    4. Verify thumbnails, metadata, and status polling
    5. Review media list and delete an item
    """
    headers = contractor_headers

    # 1. Create Demolition Site with Building Dimensions
    site_payload = {
        "name": "Midwest Industrial Silo Demolition",
        "site_code": "MIS-2026",
        "address": "400 Terminal Way",
        "city": "Gary",
        "state": "IN",
        "country": "USA",
        "building_type": "Industrial Silo",
        "building_length_m": 45.0,
        "building_width_m": 25.0,
        "building_height_m": 30.0,
        "number_of_floors": 4,
        "total_building_volume_m3": 33750.0,
        "footprint_sqm": 1125.0,
        "structural_type": "Reinforced Concrete",
    }
    site_res = await async_client.post("/api/v1/sites/", json=site_payload, headers=headers)
    assert site_res.status_code == 201, site_res.text
    site_data = site_res.json()
    assert site_data["building_type"] == "Industrial Silo"
    assert site_data["total_building_volume_m3"] == 33750.0
    site_id = site_data["id"]

    # 2. Create Site Survey Assessment
    survey_payload = {
        "site_id": site_id,
        "survey_date": "2026-11-12",
        "assessment_name": "Phase 1 Pre-Demolition Structural Drone Survey",
        "assessment_type": "PRE_DEMOLITION",
        "weather_condition": "Clear, 15°C, 8kt wind",
        "survey_notes": "Flight 1 covered northern and eastern concrete facades.",
    }
    survey_res = await async_client.post("/api/v1/surveys/", json=survey_payload, headers=headers)
    assert survey_res.status_code == 201, survey_res.text
    survey_id = survey_res.json()["id"]

    # 3. Upload Multiple Media (Photos + Synthetic Video)
    img1_bytes = create_synthetic_jpeg(640, 480, (200, 100, 50))
    img2_bytes = create_synthetic_jpeg(800, 600, (50, 150, 200))
    vid_path = create_synthetic_mp4(320, 240, fps=10, num_frames=15)

    try:
        with open(vid_path, "rb") as vf:
            vid_bytes = vf.read()

        upload_files = [
            ("files", ("silo_north_elevation.jpg", img1_bytes, "image/jpeg")),
            ("files", ("silo_interior_beam.jpg", img2_bytes, "image/jpeg")),
            ("files", ("drone_flight_orbit.mp4", vid_bytes, "video/mp4")),
        ]
        data = {
            "camera_altitude_m": "35.0",
            "focal_length_mm": "8.8",
            "sensor_width_mm": "13.2",
            "interval_seconds": "0.5",
        }

        upload_res = await async_client.post(
            f"/api/v1/surveys/{survey_id}/upload-media",
            files=upload_files,
            data=data,
            headers=headers,
        )
        assert upload_res.status_code == 200, upload_res.text
        batch_data = upload_res.json()
        assert batch_data["uploaded_count"] == 3
        assert batch_data["failed_count"] == 0
        assert len(batch_data["images"]) >= 3  # Photos + video + extracted frames

        # 4. Check Survey Status Polling
        status_res = await async_client.get(f"/api/v1/surveys/{survey_id}/media-status", headers=headers)
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["processing_status"] == "MEDIA_READY"
        assert status_data["progress_percentage"] == 100
        assert status_data["total_images_count"] >= 3

        # 5. List Media for Review
        media_res = await async_client.get(f"/api/v1/surveys/{survey_id}/media", headers=headers)
        assert media_res.status_code == 200
        media_list = media_res.json()
        assert len(media_list) >= 3

        first_img = media_list[0]
        assert first_img["download_url"] is not None
        assert first_img["thumbnail_url"] is not None

        # 6. Delete Media Item
        del_res = await async_client.delete(
            f"/api/v1/surveys/{survey_id}/media/{first_img['id']}",
            headers=headers,
        )
        assert del_res.status_code == 204

        # Confirm it was removed from active media list
        media_after = await async_client.get(f"/api/v1/surveys/{survey_id}/media", headers=headers)
        active_ids = [m["id"] for m in media_after.json()]
        assert first_img["id"] not in active_ids

    finally:
        if os.path.exists(vid_path):
            os.remove(vid_path)
