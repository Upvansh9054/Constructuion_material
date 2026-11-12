import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ai_pipeline.contracts import TrainingConfig, TrainingMetrics
from ai_pipeline.dataset_annotator import dataset_annotator

logger = logging.getLogger(__name__)


class DatasetNotReadyError(ValueError):
    """Raised when training is attempted without a valid labelled dataset."""
    pass


class DemolitionTrainingPipeline:
    """
    Production-grade model training and fine-tuning pipeline for construction
    and demolition material detection and instance segmentation.
    Uses Ultralytics YOLO with PyTorch.
    """

    def __init__(self, default_weights_dir: str = "ai_pipeline/weights"):
        self.default_weights_dir = Path(default_weights_dir)
        self.default_weights_dir.mkdir(parents=True, exist_ok=True)
        self.active_training_job_id: Optional[str] = None

    def check_training_readiness(self, dataset_dir_or_yaml: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifies if a dataset is ready for model fine-tuning.
        Returns (is_ready, message, details).
        Strict requirement: Does NOT fabricate metrics or claim unlabelled data can be trained.
        """
        p = Path(dataset_dir_or_yaml)
        dataset_dir = p.parent if p.suffix in (".yaml", ".yml") else p

        if not dataset_dir.exists():
            return False, f"Dataset path '{dataset_dir}' does not exist on disk.", {}

        validation = dataset_annotator.validate_dataset(str(dataset_dir))

        if not validation.is_valid:
            reasons = "; ".join(validation.errors + validation.warnings)
            msg = (
                f"Dataset at '{dataset_dir}' is not ready for training. "
                f"Production model fine-tuning requires labelled ground-truth demolition images. "
                f"Issues: {reasons}"
            )
            return False, msg, {
                "train_count": validation.train_count,
                "val_count": validation.val_count,
                "class_distribution": validation.class_distribution,
                "errors": validation.errors,
                "warnings": validation.warnings,
            }

        return True, f"Dataset is valid with {validation.train_count} training samples across 6 classes.", {
            "train_count": validation.train_count,
            "val_count": validation.val_count,
            "class_distribution": validation.class_distribution,
        }

    def train(self, config: Optional[TrainingConfig] = None) -> TrainingMetrics:
        """
        Executes fine-tuning of YOLO detection/segmentation model.
        Uses Ultralytics PyTorch backend.
        """
        config = config or TrainingConfig()
        yaml_path = Path(config.dataset_yaml_path)

        if not yaml_path.exists():
            raise DatasetNotReadyError(
                f"Dataset configuration '{yaml_path}' not found. "
                "Please configure a labelled demolition dataset before launching training."
            )

        # Check readiness
        is_ready, msg, details = self.check_training_readiness(str(yaml_path.parent))
        if not is_ready:
            raise DatasetNotReadyError(msg)

        logger.info(
            f"Initiating YOLO fine-tuning: base_model={config.base_model}, "
            f"epochs={config.epochs}, batch={config.batch_size}, imgsz={config.imgsz}, device={config.device}"
        )

        try:
            from ultralytics import YOLO
        except ImportError:
            raise RuntimeError("Ultralytics package is not installed. Please install torch and ultralytics.")

        start_time = time.time()

        # Load base pretrained model
        model = YOLO(config.base_model)

        # Launch real Ultralytics training
        project_dir = Path("ai_pipeline/runs/train")
        project_dir.mkdir(parents=True, exist_ok=True)

        results = model.train(
            data=str(yaml_path.resolve()),
            epochs=config.epochs,
            batch=config.batch_size,
            imgsz=config.imgsz,
            device=config.device,
            optimizer=config.optimizer,
            lr0=config.learning_rate,
            patience=config.patience,
            project=str(project_dir),
            name="demolition_run",
            exist_ok=True,
            verbose=False,
        )

        duration = time.time() - start_time

        # Extract genuine validation metrics from results
        metrics_dict: Dict[str, Any] = getattr(results, "results_dict", {})
        mAP50 = float(metrics_dict.get("metrics/mAP50(B)", 0.0))
        mAP50_95 = float(metrics_dict.get("metrics/mAP50-95(B)", 0.0))
        precision = float(metrics_dict.get("metrics/precision(B)", 0.0))
        recall = float(metrics_dict.get("metrics/recall(B)", 0.0))
        loss = float(metrics_dict.get("train/box_loss", 0.0))

        # Copy best weights to production weights folder
        best_pt_src = project_dir / "demolition_run" / "weights" / "best.pt"
        best_pt_dest = Path(config.output_weights_dir) / "demolition_materials_yolov8.pt"
        best_pt_dest.parent.mkdir(parents=True, exist_ok=True)

        if best_pt_src.exists():
            import shutil
            shutil.copy(best_pt_src, best_pt_dest)
            final_weights_path = str(best_pt_dest)
        else:
            final_weights_path = str(best_pt_src)

        logger.info(f"Training completed in {duration:.1f}s. mAP50: {mAP50:.3f}, mAP50-95: {mAP50_95:.3f}")

        return TrainingMetrics(
            epochs_completed=config.epochs,
            precision=round(precision, 4),
            recall=round(recall, 4),
            mAP50=round(mAP50, 4),
            mAP50_95=round(mAP50_95, 4),
            class_metrics={},
            best_weights_path=final_weights_path,
            training_duration_seconds=round(duration, 2),
            loss=round(loss, 4),
        )


training_pipeline = DemolitionTrainingPipeline()

