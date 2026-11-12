from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.constants import ConditionGrade, JobStatus, MaterialCategory


class DetectionBoxDTO(BaseModel):
    x_min: float = Field(..., ge=0.0, le=1.0)
    y_min: float = Field(..., ge=0.0, le=1.0)
    x_max: float = Field(..., ge=0.0, le=1.0)
    y_max: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    category: MaterialCategory
    subcategory: Optional[str] = None
    class_id: int = 0
    mask_polygon: Optional[List[List[float]]] = None
    area_pixels: Optional[float] = None


class SingleImageInferenceResponse(BaseModel):
    image_id: Optional[str] = None
    file_name: Optional[str] = None
    model_version: str
    model_architecture: str
    inference_latency_ms: float
    image_width: int
    image_height: int
    is_fine_tuned: bool
    warning: Optional[str] = None
    detections: List[DetectionBoxDTO] = []
    annotated_download_url: Optional[str] = None


class MaterialLabelCorrectionRequest(BaseModel):
    material_item_id: str
    corrected_category: MaterialCategory
    corrected_subcategory: Optional[str] = None
    condition_grade: Optional[ConditionGrade] = None
    notes: Optional[str] = None
    save_to_training_pool: bool = True


class MaterialLabelCorrectionResponse(BaseModel):
    material_item_id: str
    previous_category: MaterialCategory
    updated_category: MaterialCategory
    is_verified: bool
    training_sample_saved: bool
    training_dataset_path: Optional[str] = None


class ModelEvaluationDTO(BaseModel):
    model_name: str
    architecture: str
    parameter_count_millions: float
    mAP50_coco_baseline: float
    latency_cpu_ms: float
    latency_gpu_ms: float
    memory_footprint_mb: float
    segmentation_capable: bool
    demolition_suitability_grade: str
    evaluation_notes: str


class TrainingPipelineTriggerRequest(BaseModel):
    base_model: str = Field(default="yolov8s.pt", description="Base pretrained model backbone")
    dataset_yaml_path: str = Field(
        default="ai_pipeline/datasets/demolition_materials.yaml",
        description="Path to dataset configuration YAML",
    )
    epochs: int = Field(default=30, ge=1, le=300)
    batch_size: int = Field(default=16, ge=1, le=128)
    imgsz: int = Field(default=640, ge=320, le=1920)
    learning_rate: float = Field(default=0.01, ge=0.0001, le=0.1)
    device: str = Field(default="cpu")


class TrainingPipelineResponse(BaseModel):
    success: bool
    message: str
    metrics: Optional[Dict[str, Any]] = None
    dataset_readiness: Dict[str, Any] = {}


class DatasetStatsResponse(BaseModel):
    is_ready_for_training: bool
    train_count: int
    val_count: int
    class_distribution: Dict[str, int]
    classes: List[str]
    errors: List[str] = []
    warnings: List[str] = []


class AnalysisJobTriggerRequest(BaseModel):
    survey_id: str
    run_volumetric_estimation: bool = True
    generate_summary_report: bool = True
    confidence_threshold: Optional[float] = Field(default=0.40, ge=0.1, le=1.0)


class AnalysisJobResponse(BaseModel):
    id: str
    survey_id: str
    celery_task_id: Optional[str] = None
    status: JobStatus
    progress_percentage: int
    processed_images_count: int
    total_images_count: int
    error_message: Optional[str] = None
    execution_metrics: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DemolitionAuditReportResponse(BaseModel):
    id: str
    site_id: str
    survey_id: str
    report_title: str
    executive_summary: str
    regulatory_compliance_notes: Optional[str] = None
    buyer_matching_insights: Optional[str] = None
    total_recoverable_tonnes: float
    total_estimated_value_usd: float
    total_carbon_offset_kg_co2e: float
    detailed_breakdown_json: Dict[str, Any]
    pdf_report_s3_key: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
