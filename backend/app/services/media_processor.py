import io
import logging
import math
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import ExifTags, Image, ImageOps
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import JobStatus, MediaType, SurveyStatus
from app.models.analysis_job import AnalysisJob
from app.models.survey import SiteSurvey, SurveyImage
from app.services.storage import storage_service

logger = logging.getLogger(__name__)

# Supported formats & thresholds
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

MAX_IMAGE_SIZE_BYTES = 50 * 1024 * 1024       # 50 MB
MAX_VIDEO_SIZE_BYTES = 500 * 1024 * 1024      # 500 MB
THUMBNAIL_MAX_DIMENSION = 320
CV_PREPROCESS_MAX_DIMENSION = 1920


@dataclass
class ImageValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    focal_length_mm: Optional[float] = None
    camera_model: Optional[str] = None


@dataclass
class VideoValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None
    codec: Optional[str] = None


class MediaProcessingError(Exception):
    """Custom exception raised during media validation or processing."""
    pass


class MediaProcessorService:
    """
    Production-grade image & video processing engine:
    - Robust format and corruption validation
    - EXIF GPS and camera parameter extraction
    - High-quality thumbnail generation
    - CV-ready image normalization (EXIF rotation correction, resizing)
    - Video keyframe extraction at configurable intervals
    - Near-duplicate frame rejection (MAD/MSE comparison)
    """

    @staticmethod
    def _convert_dms_to_degrees(dms_values, ref: str) -> Optional[float]:
        """Convert degrees/minutes/seconds GPS rational tuple to decimal degrees."""
        try:
            d = float(dms_values[0])
            m = float(dms_values[1])
            s = float(dms_values[2])
            deg = d + (m / 60.0) + (s / 3600.0)
            if ref in ("S", "W"):
                deg = -deg
            return round(deg, 6)
        except Exception:
            return None

    @classmethod
    def extract_image_metadata(cls, image_bytes: bytes) -> ImageValidationResult:
        """Validate image bytes, check for corruption, and extract resolution & EXIF metadata."""
        if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
            return ImageValidationResult(
                is_valid=False,
                error_message=f"Image file size ({len(image_bytes)/(1024*1024):.1f}MB) exceeds limit of 50MB.",
            )

        try:
            # Step 1: PIL verify for corruption check
            bio = io.BytesIO(image_bytes)
            img = Image.open(bio)
            img.verify()

            # Step 2: Reopen to read attributes & EXIF
            bio.seek(0)
            img = Image.open(bio)
            w, h = img.size

            # Extract EXIF tags
            gps_lat = None
            gps_lon = None
            focal_mm = None
            camera_model = None

            exif = img.getexif()
            if exif:
                # Camera Model
                camera_model = exif.get(ExifTags.Base.Model.value)

                # Focal Length
                focal_val = exif.get(ExifTags.Base.FocalLength.value)
                if focal_val:
                    try:
                        focal_mm = float(focal_val)
                    except Exception:
                        pass

                # GPS IFD
                gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo.value)
                if gps_ifd:
                    lat_dms = gps_ifd.get(ExifTags.GPS.GPSLatitude.value)
                    lat_ref = gps_ifd.get(ExifTags.GPS.GPSLatitudeRef.value, "N")
                    lon_dms = gps_ifd.get(ExifTags.GPS.GPSLongitude.value)
                    lon_ref = gps_ifd.get(ExifTags.GPS.GPSLongitudeRef.value, "E")

                    if lat_dms and lon_dms:
                        gps_lat = cls._convert_dms_to_degrees(lat_dms, lat_ref)
                        gps_lon = cls._convert_dms_to_degrees(lon_dms, lon_ref)

            return ImageValidationResult(
                is_valid=True,
                width=w,
                height=h,
                gps_latitude=gps_lat,
                gps_longitude=gps_lon,
                focal_length_mm=focal_mm,
                camera_model=camera_model,
            )

        except Exception as e:
            logger.warning(f"Image validation/corruption check failed: {e}")
            return ImageValidationResult(
                is_valid=False,
                error_message=f"Corrupt or unsupported image stream: {str(e)}",
            )

    @classmethod
    def generate_image_derivatives(cls, image_bytes: bytes) -> Tuple[bytes, bytes, int, int]:
        """
        Generates thumbnail bytes and CV-preprocessed normalized bytes.
        Returns (thumbnail_bytes, cv_bytes, final_width, final_height).
        """
        img = Image.open(io.BytesIO(image_bytes))
        # 1. Correct EXIF orientation (drone/mobile captures)
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            img = img.convert("RGB")

        orig_w, orig_h = img.size

        # 2. Thumbnail (max 320x320)
        thumb_img = img.copy()
        thumb_img.thumbnail((THUMBNAIL_MAX_DIMENSION, THUMBNAIL_MAX_DIMENSION), Image.Resampling.LANCZOS)
        thumb_buf = io.BytesIO()
        thumb_img.save(thumb_buf, format="JPEG", quality=85, optimize=True)
        thumb_bytes = thumb_buf.getvalue()

        # 3. CV Preprocessed image (max 1920px longest edge for fast YOLO inference)
        cv_img = img.copy()
        max_dim = max(orig_w, orig_h)
        if max_dim > CV_PREPROCESS_MAX_DIMENSION:
            scale = CV_PREPROCESS_MAX_DIMENSION / float(max_dim)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            cv_img = cv_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            new_w, new_h = orig_w, orig_h

        cv_buf = io.BytesIO()
        cv_img.save(cv_buf, format="JPEG", quality=90, optimize=True)
        cv_bytes = cv_buf.getvalue()

        return thumb_bytes, cv_bytes, new_w, new_h

    @classmethod
    def validate_video_file(cls, video_path: str) -> VideoValidationResult:
        """Validate video file with OpenCV and extract resolution, duration, FPS, and codec."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return VideoValidationResult(
                is_valid=False,
                error_message="Unsupported video codec or corrupted video container.",
            )

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC) or 0)
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

            # Verify at least one frame can be read
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                return VideoValidationResult(
                    is_valid=False,
                    error_message="Video contains zero readable frames.",
                )

            duration = (frame_count / fps) if fps > 0 else 0.0

            return VideoValidationResult(
                is_valid=True,
                width=width,
                height=height,
                duration_seconds=round(duration, 2),
                fps=round(fps, 2),
                frame_count=frame_count,
                codec=codec.strip(),
            )
        finally:
            cap.release()

    @classmethod
    def are_frames_similar(cls, frame_a: np.ndarray, frame_b: np.ndarray, threshold: float = 0.97) -> bool:
        """
        Evaluates whether two frames are duplicate / near-static.
        Downscales to 64x64 grayscale and computes normalized Mean Absolute Difference (MAD).
        Returns True if frames are near identical (difference < (1.0 - threshold)).
        """
        gray_a = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
        gray_b = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)

        thumb_a = cv2.resize(gray_a, (64, 64), interpolation=cv2.INTER_AREA)
        thumb_b = cv2.resize(gray_b, (64, 64), interpolation=cv2.INTER_AREA)

        mad = np.mean(np.abs(thumb_a.astype(np.float32) - thumb_b.astype(np.float32))) / 255.0
        similarity = 1.0 - mad
        return similarity >= threshold

    @classmethod
    def extract_video_frames(
        cls,
        video_path: str,
        interval_seconds: float = 1.0,
        similarity_threshold: float = 0.97,
        max_frames: int = 120,
    ) -> List[Dict[str, Any]]:
        """
        Extracts representative non-redundant frames from video at configured intervals.
        Returns a list of extracted frame metadata dictionaries containing:
        - frame_index: int
        - timestamp_seconds: float
        - frame_bgr: np.ndarray
        - width: int
        - height: int
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise MediaProcessingError("Failed to open video for frame extraction.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_step = max(1, int(round(fps * interval_seconds)))

        extracted: List[Dict[str, Any]] = []
        last_retained_frame: Optional[np.ndarray] = None
        current_frame_idx = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                if current_frame_idx % frame_step == 0:
                    timestamp = round(current_frame_idx / fps, 2)

                    # Deduplication check
                    is_duplicate = False
                    if last_retained_frame is not None:
                        if cls.are_frames_similar(frame, last_retained_frame, threshold=similarity_threshold):
                            is_duplicate = True

                    if not is_duplicate:
                        h, w = frame.shape[:2]
                        extracted.append({
                            "frame_index": current_frame_idx,
                            "timestamp_seconds": timestamp,
                            "frame_bgr": frame.copy(),
                            "width": w,
                            "height": h,
                        })
                        last_retained_frame = frame

                        if len(extracted) >= max_frames:
                            logger.info(f"Reached max frame extraction limit ({max_frames} frames).")
                            break

                current_frame_idx += 1

        finally:
            cap.release()

        return extracted

    @classmethod
    async def process_survey_image(
        cls,
        session: AsyncSession,
        image_record: SurveyImage,
        image_bytes: bytes,
    ) -> SurveyImage:
        """Process a single image record: validates, generates thumbnail & CV derivative, uploads to storage."""
        meta = cls.extract_image_metadata(image_bytes)
        if not meta.is_valid:
            image_record.processing_status = "FAILED"
            image_record.error_message = meta.error_message or "Invalid image file"
            await session.commit()
            return image_record

        try:
            thumb_bytes, cv_bytes, final_w, final_h = cls.generate_image_derivatives(image_bytes)

            survey_id = image_record.survey_id
            thumb_key = f"thumbnails/{survey_id}/{image_record.id}.jpg"
            cv_key = f"cv_preprocessed/{survey_id}/{image_record.id}.jpg"

            storage_service.upload_bytes(thumb_bytes, thumb_key, content_type="image/jpeg")
            storage_service.upload_bytes(cv_bytes, cv_key, content_type="image/jpeg")

            image_record.thumbnail_s3_key = thumb_key
            image_record.cv_preprocessed_s3_key = cv_key
            image_record.width = meta.width or final_w
            image_record.height = meta.height or final_h
            if meta.gps_latitude is not None:
                image_record.gps_latitude = meta.gps_latitude
            if meta.gps_longitude is not None:
                image_record.gps_longitude = meta.gps_longitude
            if meta.focal_length_mm is not None and not image_record.focal_length_mm:
                image_record.focal_length_mm = meta.focal_length_mm

            image_record.processing_status = "PROCESSED"
            image_record.error_message = None

            # Fetch survey to increment processed counter
            survey_res = await session.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
            survey = survey_res.scalar_one_or_none()
            if survey:
                survey.processed_images_count += 1

            await session.commit()
            return image_record

        except Exception as e:
            logger.error(f"Error generating derivatives for image {image_record.id}: {e}")
            image_record.processing_status = "FAILED"
            image_record.error_message = str(e)
            await session.commit()
            return image_record

    @classmethod
    async def process_survey_video(
        cls,
        session: AsyncSession,
        video_record: SurveyImage,
        video_bytes: bytes,
        interval_seconds: float = 1.0,
        similarity_threshold: float = 0.97,
    ) -> List[SurveyImage]:
        """Validate video, extract non-redundant frames, upload frame derivatives and create child SurveyImage records."""
        suffix = Path(video_record.file_name).suffix or ".mp4"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(video_bytes)

        try:
            val = cls.validate_video_file(tmp_path)
            if not val.is_valid:
                video_record.processing_status = "FAILED"
                video_record.error_message = val.error_message or "Invalid video stream"
                await session.commit()
                return []

            video_record.width = val.width
            video_record.height = val.height
            video_record.duration_seconds = val.duration_seconds
            video_record.fps = val.fps
            video_record.codec = val.codec
            video_record.processing_status = "PROCESSED"

            # Extract deduplicated frames
            frames = cls.extract_video_frames(
                tmp_path,
                interval_seconds=interval_seconds,
                similarity_threshold=similarity_threshold,
            )

            survey_id = video_record.survey_id
            survey_res = await session.execute(select(SiteSurvey).filter(SiteSurvey.id == survey_id))
            survey = survey_res.scalar_one_or_none()

            created_frames: List[SurveyImage] = []

            for f_data in frames:
                frame_bgr = f_data["frame_bgr"]
                frame_idx = f_data["frame_index"]
                timestamp = f_data["timestamp_seconds"]

                success, enc_buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
                if not success:
                    continue

                frame_bytes = enc_buf.tobytes()
                frame_id = str(uuid.uuid4())
                frame_orig_key = f"frames/{survey_id}/{frame_id}.jpg"
                storage_service.upload_bytes(frame_bytes, frame_orig_key, content_type="image/jpeg")

                # Generate thumbnail and CV derivative
                thumb_bytes, cv_bytes, fw, fh = cls.generate_image_derivatives(frame_bytes)
                thumb_key = f"thumbnails/{survey_id}/{frame_id}.jpg"
                cv_key = f"cv_preprocessed/{survey_id}/{frame_id}.jpg"
                storage_service.upload_bytes(thumb_bytes, thumb_key, content_type="image/jpeg")
                storage_service.upload_bytes(cv_bytes, cv_key, content_type="image/jpeg")

                # If video has no thumbnail yet, use the first frame
                if not video_record.thumbnail_s3_key:
                    video_record.thumbnail_s3_key = thumb_key

                frame_rec = SurveyImage(
                    id=frame_id,
                    survey_id=survey_id,
                    parent_video_id=video_record.id,
                    file_name=f"{video_record.file_name}_frame_{frame_idx:04d}.jpg",
                    media_type=MediaType.IMAGE,
                    original_s3_key=frame_orig_key,
                    thumbnail_s3_key=thumb_key,
                    cv_preprocessed_s3_key=cv_key,
                    file_size_bytes=len(frame_bytes),
                    mime_type="image/jpeg",
                    width=fw,
                    height=fh,
                    is_extracted_frame=True,
                    frame_index=frame_idx,
                    timestamp_seconds=timestamp,
                    processing_status="PROCESSED",
                    camera_altitude_m=video_record.camera_altitude_m,
                    focal_length_mm=video_record.focal_length_mm,
                    sensor_width_mm=video_record.sensor_width_mm,
                    gsd_cm_per_px=video_record.gsd_cm_per_px,
                    gps_latitude=video_record.gps_latitude,
                    gps_longitude=video_record.gps_longitude,
                )
                session.add(frame_rec)
                created_frames.append(frame_rec)

            if survey:
                survey.extracted_frames_count += len(created_frames)
                survey.total_images_count += len(created_frames)
                survey.processed_images_count += len(created_frames)

            await session.commit()
            return created_frames

        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass


media_processor = MediaProcessorService()
