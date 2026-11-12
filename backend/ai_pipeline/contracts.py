from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from app.core.constants import ConditionGrade, MaterialCategory


@dataclass
class DetectionBox:
    """Represents a localized material object in an image with optional segmentation polygon."""
    x_min: float  # Normalized coordinates [0.0, 1.0]
    y_min: float
    x_max: float
    y_max: float
    confidence: float
    category: MaterialCategory
    subcategory: Optional[str] = None
    class_id: int = 0
    mask_polygon: Optional[List[List[float]]] = None  # Normalized polygon vertices [[x1, y1], [x2, y2], ...]
    area_pixels: Optional[float] = None
    tracking_id: Optional[int] = None


@dataclass
class MaterialPredictionResult:
    """Encapsulates the complete inference output for an image."""
    detections: List[DetectionBox]
    model_version: str
    model_architecture: str
    inference_latency_ms: float
    image_width: int
    image_height: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    annotated_s3_key: Optional[str] = None
    is_fine_tuned: bool = False
    warning: Optional[str] = None


@dataclass
class ModelEvaluationReport:
    """Benchmark performance report across candidate detection/segmentation backbones."""
    model_name: str
    architecture: str
    parameter_count_millions: float
    mAP50_coco_baseline: float
    latency_cpu_ms: float
    latency_gpu_ms: float
    memory_footprint_mb: float
    segmentation_capable: bool
    demolition_suitability_grade: str  # e.g. "RECOMMENDED_EDGE", "RECOMMENDED_CLOUD", "EXPERIMENTAL"
    evaluation_notes: str


@dataclass
class TrainingConfig:
    """Hyperparameters and configuration for the fine-tuning pipeline."""
    base_model: str = "yolov8s.pt"  # Pretrained weights starting point
    dataset_yaml_path: str = "ai_pipeline/datasets/demolition_materials.yaml"
    epochs: int = 50
    batch_size: int = 16
    imgsz: int = 640
    learning_rate: float = 0.01
    optimizer: str = "AdamW"
    device: str = "cpu"  # "cpu", "cuda:0"
    patience: int = 10   # Early stopping patience
    save_period: int = 5
    augment: bool = True
    output_weights_dir: str = "ai_pipeline/weights"


@dataclass
class TrainingMetrics:
    """Evaluated validation metrics upon completion of a fine-tuning run."""
    epochs_completed: int
    precision: float
    recall: float
    mAP50: float
    mAP50_95: float
    class_metrics: Dict[str, Dict[str, float]]
    best_weights_path: str
    training_duration_seconds: float
    loss: float


@dataclass
class DatasetValidationResult:
    """Report on dataset structure and annotation integrity."""
    is_valid: bool
    train_count: int = 0
    val_count: int = 0
    test_count: int = 0
    class_distribution: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class QuantityEstimate:
    """Volumetric and mass estimates derived from spatial bounds and density tables."""
    volume_m3: float
    weight_tonnes: float
    surface_area_m2: Optional[float] = None
    unit_count: Optional[int] = None
    estimation_method: str = "geometric_projection"


@dataclass
class QuantityEstimateExtended:
    """
    Comprehensive physical dimensional, volumetric, and mass estimate
    with uncertainty bounds and full disclosure of assumptions.
    """
    nominal_volume_m3: float
    nominal_weight_tonnes: float
    min_volume_m3: float
    max_volume_m3: float
    min_weight_tonnes: float
    max_weight_tonnes: float
    uncertainty_percentage: float
    length_m: float
    width_m: float
    height_m: float
    surface_area_m2: float
    assumed_density_t_per_m3: float
    packing_factor: float
    estimation_method: str
    assumptions_applied: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionAssessment:
    """Physical condition grading and safety/contamination flags."""
    grade: ConditionGrade
    confidence: float
    hazard_flags: List[str] = field(default_factory=list)
    inspection_notes: Optional[str] = None


@dataclass
class ConditionAssessmentExtended:
    """
    Detailed material condition, visible damage quantification,
    contamination hazards (Asbestos ACM, Lead, Creosote), and circular economy recovery routing.
    """
    grade: ConditionGrade
    damage_severity_pct: float
    damage_type: Optional[str] = None
    contamination_risk: Optional[str] = None
    requires_specialist_abatement: bool = False
    hazard_inspection_warning: Optional[str] = None
    recommended_recovery_route: str = "CLOSED_LOOP_RECYCLING"
    recoverability_percentage: float = 85.0
    inspection_notes: str = ""
    confidence: float = 0.85
    indicators: List[str] = field(default_factory=list)


@dataclass
class MultiViewReconstructionResult:
    """3D photogrammetric point cloud reconstruction result."""
    point_count: int
    bounding_box_3d: Dict[str, float]
    convex_hull_volume_m3: float
    reconstruction_confidence: float
    matched_features_count: int
    triangulation_error_px: float
    methodology_used: str
    point_cloud_summary: Optional[Dict[str, Any]] = None


class BaseMaterialDetector(ABC):
    """Contract for computer vision material object detection models."""

    @abstractmethod
    def load_model(self) -> None:
        """Loads weights into memory or device (CPU/CUDA)."""
        pass

    @abstractmethod
    def detect(
        self,
        image_bgr: np.ndarray,
        confidence_threshold: float = 0.45,
        iou_threshold: float = 0.50,
    ) -> List[DetectionBox]:
        """Runs visual inference on a single BGR image array."""
        pass


class BaseQuantityEstimator(ABC):
    """Contract for calculating material volume and weight from 2D bounding boxes and camera metadata."""

    @abstractmethod
    def estimate(
        self,
        box: DetectionBox,
        image_shape: Tuple[int, int, int],  # (height, width, channels)
        camera_height_meters: Optional[float] = None,
        focal_length_mm: Optional[float] = None,
        sensor_width_mm: Optional[float] = None,
        depth_map: Optional[np.ndarray] = None,
    ) -> QuantityEstimate:
        pass


class BaseConditionClassifier(ABC):
    """Contract for evaluating material condition, wear, and contamination risks."""

    @abstractmethod
    def assess(
        self,
        crop_bgr: np.ndarray,
        category: MaterialCategory,
    ) -> ConditionAssessment:
        pass
