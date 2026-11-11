import logging
import os
from typing import Dict, List, Optional
import numpy as np
from app.core.constants import MaterialCategory
from ai_pipeline.contracts import BaseMaterialDetector, DetectionBox

logger = logging.getLogger(__name__)


class ModelWeightsNotFoundError(FileNotFoundError):
    """Raised when the fine-tuned material detection weights file is missing."""
    pass


# Mapping from YOLO class label/index to domain MaterialCategory
DEFAULT_CLASS_MAPPING: Dict[str, MaterialCategory] = {
    "concrete": MaterialCategory.CONCRETE,
    "bricks": MaterialCategory.BRICKS,
    "brick": MaterialCategory.BRICKS,
    "steel": MaterialCategory.STEEL,
    "rebar": MaterialCategory.STEEL,
    "timber": MaterialCategory.TIMBER,
    "wood": MaterialCategory.TIMBER,
    "glass": MaterialCategory.GLASS,
    "mixed_debris": MaterialCategory.MIXED_DEBRIS,
    "rubble": MaterialCategory.MIXED_DEBRIS,
}


class YOLOMaterialDetector(BaseMaterialDetector):
    """
    Production YOLO (v8/v11) detector for demolition site visual analysis.
    Uses Ultralytics PyTorch runtime.
    """

    def __init__(
        self,
        weights_path: str = "ai_pipeline/weights/demolition_materials_yolov8.pt",
        allow_cpu_fallback: bool = True,
    ):
        self.weights_path = weights_path
        self.allow_cpu_fallback = allow_cpu_fallback
        self.model = None
        self._is_ready = False

    def is_weights_available(self) -> bool:
        return os.path.exists(self.weights_path)

    def load_model(self) -> None:
        """
        Loads the trained YOLO model into memory.
        Raises ModelWeightsNotFoundError if the trained model has not yet been placed in the weights folder.
        """
        if not self.is_weights_available():
            raise ModelWeightsNotFoundError(
                f"Trained YOLO weights file was not found at '{self.weights_path}'. "
                f"Please place your fine-tuned weights file (e.g. demolition_materials_yolov8.pt) "
                f"in 'backend/ai_pipeline/weights/' or download from model registry. "
                f"See backend/ai_pipeline/README.md for dataset training instructions."
            )

        try:
            from ultralytics import YOLO
            logger.info(f"Loading YOLO material detection model from {self.weights_path}...")
            self.model = YOLO(self.weights_path)
            self._is_ready = True
            logger.info("YOLO material detection model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize YOLO model: {e}")
            raise

    def detect(
        self,
        image_bgr: np.ndarray,
        confidence_threshold: float = 0.45,
        iou_threshold: float = 0.50,
    ) -> List[DetectionBox]:
        """
        Executes real computer vision object detection on the input BGR image.
        Returns a list of DetectionBox items with normalized coordinates.
        """
        if not self._is_ready or self.model is None:
            self.load_model()

        h, w = image_bgr.shape[:2]
        results = self.model.predict(
            source=image_bgr,
            conf=confidence_threshold,
            iou=iou_threshold,
            verbose=False,
        )

        detections: List[DetectionBox] = []
        if not results:
            return detections

        first_res = results[0]
        boxes = first_res.boxes

        if boxes is None:
            return detections

        for box in boxes:
            cls_id = int(box.cls[0].item())
            cls_name = first_res.names.get(cls_id, "").lower()
            conf = float(box.conf[0].item())

            # Map detected class to standard MaterialCategory enum
            category = DEFAULT_CLASS_MAPPING.get(cls_name, MaterialCategory.MIXED_DEBRIS)

            # xyxy returns pixel coordinates [x1, y1, x2, y2]
            xyxy = box.xyxy[0].tolist()
            x1_norm = max(0.0, min(1.0, xyxy[0] / w))
            y1_norm = max(0.0, min(1.0, xyxy[1] / h))
            x2_norm = max(0.0, min(1.0, xyxy[2] / w))
            y2_norm = max(0.0, min(1.0, xyxy[3] / h))

            detections.append(
                DetectionBox(
                    x_min=round(x1_norm, 4),
                    y_min=round(y1_norm, 4),
                    x_max=round(x2_norm, 4),
                    y_max=round(y2_norm, 4),
                    confidence=round(conf, 4),
                    category=category,
                    subcategory=cls_name if cls_name in DEFAULT_CLASS_MAPPING else None,
                )
            )

        return detections
