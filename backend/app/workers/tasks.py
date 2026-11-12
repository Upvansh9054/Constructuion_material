import asyncio
from datetime import datetime, timezone
import logging
from typing import Dict, List
import cv2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.constants import JobStatus, SurveyStatus
from app.core.database import AsyncSessionLocal
from app.models.analysis_job import AnalysisJob
from app.models.audit_report import DemolitionAuditReport
from app.models.material import MaterialItem
from app.models.site import DemolitionSite
from app.models.survey import SiteSurvey, SurveyImage
from app.services.llm_report import llm_report_service
from app.services.storage import storage_service
from app.services.valuation import valuation_service
from app.workers.celery_app import celery_app
from ai_pipeline.detector import ModelWeightsNotFoundError, YOLOMaterialDetector
from ai_pipeline.estimator import GeometricQuantityEstimator, HeuristicConditionAssessor
from ai_pipeline.preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)


async def _execute_survey_analysis_async(survey_id: str, job_id: str):
    """Internal asynchronous worker pipeline executing CV detection, estimation, and audit synthesis."""
    detector = YOLOMaterialDetector(weights_path=settings.YOLO_MODEL_PATH)
    estimator = GeometricQuantityEstimator()
    assessor = HeuristicConditionAssessor()

    async with AsyncSessionLocal() as session:
        # 1. Fetch analysis job and survey
        job_result = await session.execute(select(AnalysisJob).filter(AnalysisJob.id == job_id))
        job = job_result.scalar_one_or_none()
        if not job:
            logger.error(f"Analysis job {job_id} not found.")
            return

        survey_result = await session.execute(
            select(SiteSurvey).filter(SiteSurvey.id == survey_id)
        )
        survey = survey_result.scalar_one_or_none()
        if not survey:
            job.status = JobStatus.FAILED
            job.error_message = f"Survey {survey_id} not found."
            await session.commit()
            return

        site_result = await session.execute(
            select(DemolitionSite).filter(DemolitionSite.id == survey.site_id)
        )
        site = site_result.scalar_one_or_none()

        job.status = JobStatus.IN_PROGRESS
        job.started_at = datetime.now(timezone.utc)
        survey.status = SurveyStatus.PROCESSING
        await session.commit()

        # 2. Check model weights availability & mode notice
        if not detector.is_weights_available():
            logger.info(
                f"Fine-tuned weights not found at '{settings.YOLO_MODEL_PATH}'. "
                "Executing Demolition Computer Vision detection engine with Human-in-the-Loop review."
            )

        # 3. Fetch images for this survey
        images_result = await session.execute(
            select(SurveyImage).filter(SurveyImage.survey_id == survey_id)
        )
        images = list(images_result.scalars().all())
        total_images = len(images)
        job.total_images_count = total_images

        if total_images == 0:
            job.status = JobStatus.FAILED
            job.error_message = "No survey images found to analyze."
            survey.status = SurveyStatus.FAILED
            await session.commit()
            return

        created_items: List[MaterialItem] = []
        processed_count = 0

        for img_record in images:
            try:
                # Download raw image bytes from S3
                raw_bytes = storage_service.download_bytes(img_record.original_s3_key)
                bgr_img = ImagePreprocessor.decode_from_bytes(raw_bytes)
                h, w = bgr_img.shape[:2]
                img_record.width = w
                img_record.height = h

                # Run real YOLO inference
                detections = detector.detect(bgr_img, confidence_threshold=settings.CONFIDENCE_THRESHOLD)

                # Process each detected material object
                for det in detections:
                    # Estimate physical quantity
                    qty = estimator.estimate(det, image_shape=bgr_img.shape)

                    # Assess condition & contamination
                    crop_y1 = int(det.y_min * h)
                    crop_y2 = int(det.y_max * h)
                    crop_x1 = int(det.x_min * w)
                    crop_x2 = int(det.x_max * w)
                    crop = bgr_img[crop_y1:crop_y2, crop_x1:crop_x2]
                    cond = assessor.assess(crop, det.category)

                    # Calculate market valuation and embodied carbon offsets
                    val_usd, carbon_kg = valuation_service.calculate_valuation(
                        category=det.category,
                        condition=cond.grade,
                        weight_tonnes=qty.weight_tonnes,
                    )

                    material_item = MaterialItem(
                        survey_id=survey.id,
                        source_image_id=img_record.id,
                        category=det.category,
                        subcategory=det.subcategory,
                        condition_grade=cond.grade,
                        estimated_volume_m3=qty.volume_m3,
                        estimated_weight_tonnes=qty.weight_tonnes,
                        unit_count=qty.unit_count,
                        contamination_risk=", ".join(cond.hazard_flags) if cond.hazard_flags else None,
                        confidence_score=det.confidence,
                        bounding_box={
                            "x_min": det.x_min,
                            "y_min": det.y_min,
                            "x_max": det.x_max,
                            "y_max": det.y_max,
                        },
                        estimated_market_value_usd=val_usd,
                        embodied_carbon_offset_kg=carbon_kg,
                    )
                    session.add(material_item)
                    created_items.append(material_item)

                # Render annotated visualization and upload back to S3
                if detections:
                    annotated_bgr = ImagePreprocessor.render_bounding_boxes(bgr_img, detections)
                    success, enc_buf = cv2.imencode(".jpg", annotated_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
                    if success:
                        annotated_key = f"annotated/{survey_id}/{img_record.id}.jpg"
                        storage_service.upload_bytes(enc_buf.tobytes(), annotated_key, content_type="image/jpeg")
                        img_record.annotated_s3_key = annotated_key

                processed_count += 1
                job.processed_images_count = processed_count
                job.progress_percentage = int((processed_count / total_images) * 80)
                await session.commit()

            except Exception as img_err:
                logger.error(f"Error processing image {img_record.id}: {img_err}")
                continue

        # 4. Generate Aggregated Audit Summary & LLM Report
        total_tonnes = sum(item.estimated_weight_tonnes for item in created_items)
        total_val_usd = sum(item.estimated_market_value_usd for item in created_items)
        total_carbon_kg = sum(item.embodied_carbon_offset_kg for item in created_items)

        material_breakdown: List[Dict] = []
        for cat in set(item.category for item in created_items):
            cat_items = [it for it in created_items if it.category == cat]
            material_breakdown.append({
                "category": cat.value,
                "count": len(cat_items),
                "total_tonnes": round(sum(it.estimated_weight_tonnes for it in cat_items), 2),
                "total_volume_m3": round(sum(it.estimated_volume_m3 for it in cat_items), 2),
                "estimated_value_usd": round(sum(it.estimated_market_value_usd for it in cat_items), 2),
                "carbon_offset_kg": round(sum(it.embodied_carbon_offset_kg for it in cat_items), 2),
            })

        site_name = site.name if site else "Demolition Site"
        site_location = f"{site.city}, {site.country}" if site else "Unknown"

        llm_insights = await llm_report_service.generate_audit_summary(
            site_name=site_name,
            site_location=site_location,
            survey_notes=survey.survey_notes,
            material_breakdown=material_breakdown,
            total_tonnes=total_tonnes,
            total_value_usd=total_val_usd,
            total_carbon_offset_kg=total_carbon_kg,
        )

        audit_report = DemolitionAuditReport(
            site_id=survey.site_id,
            survey_id=survey.id,
            report_title=f"Demolition Material Audit Report - {site_name}",
            executive_summary=llm_insights.get("executive_summary", "Audit summary complete."),
            regulatory_compliance_notes=llm_insights.get("regulatory_compliance_notes"),
            buyer_matching_insights=llm_insights.get("buyer_matching_insights"),
            total_recoverable_tonnes=round(total_tonnes, 2),
            total_estimated_value_usd=round(total_val_usd, 2),
            total_carbon_offset_kg_co2e=round(total_carbon_kg, 2),
            detailed_breakdown_json=material_breakdown,
        )
        session.add(audit_report)

        # 5. Finalize Job
        job.progress_percentage = 100
        job.status = JobStatus.SUCCESS
        job.completed_at = datetime.now(timezone.utc)
        survey.status = SurveyStatus.ANALYSIS_COMPLETED
        await session.commit()
        logger.info(f"Survey analysis {survey_id} completed successfully.")


@celery_app.task(bind=True, name="app.workers.tasks.process_survey_analysis_task")
def process_survey_analysis_task(self, survey_id: str, job_id: str):
    """Celery task entry point."""
    logger.info(f"Starting Celery task for survey_id={survey_id}, job_id={job_id}")
    asyncio.run(_execute_survey_analysis_async(survey_id, job_id))

