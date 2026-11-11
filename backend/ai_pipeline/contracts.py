from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np
from app.core.constants import ConditionGrade, MaterialCategory


@dataclass
class DetectionBox:
    """Represents a localized material object in an image."""
    x_min: float  # Normalized coordinates [0.0, 1.0]
    y_min: float
    x_max: float
    y_max: float
    confidence: float
    category: MaterialCategory
    subcategory: Optional[str] = None
    mask_polygon: Optional[List[List[float]]] = None


@dataclass
class QuantityEstimate:
    """Volumetric and mass estimates derived from spatial bounds and density tables."""
    volume_m3: float
    weight_tonnes: float
    surface_area_m2: Optional[float] = None
    unit_count: Optional[int] = None
    estimation_method: str = "geometric_projection"


@dataclass
class ConditionAssessment:
    """Physical condition grading and safety/contamination flags."""
    grade: ConditionGrade
    confidence: float
    hazard_flags: List[str] = field(default_factory=list)
    inspection_notes: Optional[str] = None


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

