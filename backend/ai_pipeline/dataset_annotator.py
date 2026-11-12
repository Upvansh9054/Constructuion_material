import io
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import yaml

from app.core.constants import MaterialCategory
from ai_pipeline.contracts import DatasetValidationResult, DetectionBox

logger = logging.getLogger(__name__)

# Standard 6 Initial Demolition Material Classes
MATERIAL_CLASS_NAMES: List[str] = [
    "concrete",      # 0
    "bricks",        # 1
    "steel",         # 2
    "timber",        # 3
    "glass",         # 4
    "mixed_debris",  # 5
]

CLASS_NAME_TO_ID: Dict[str, int] = {name: idx for idx, name in enumerate(MATERIAL_CLASS_NAMES)}
CATEGORY_TO_CLASS_ID: Dict[MaterialCategory, int] = {
    MaterialCategory.CONCRETE: 0,
    MaterialCategory.BRICKS: 1,
    MaterialCategory.STEEL: 2,
    MaterialCategory.TIMBER: 3,
    MaterialCategory.GLASS: 4,
    MaterialCategory.MIXED_DEBRIS: 5,
}
CLASS_ID_TO_CATEGORY: Dict[int, MaterialCategory] = {
    0: MaterialCategory.CONCRETE,
    1: MaterialCategory.BRICKS,
    2: MaterialCategory.STEEL,
    3: MaterialCategory.TIMBER,
    4: MaterialCategory.GLASS,
    5: MaterialCategory.MIXED_DEBRIS,
}


class DemolitionDatasetAnnotator:
    """
    Manages dataset annotation formatting, data.yaml generation,
    integrity validation, and active-learning human-in-the-loop exports.
    """

    @classmethod
    def detection_to_yolo_bbox_line(cls, box: DetectionBox) -> str:
        """
        Converts a normalized [x_min, y_min, x_max, y_max] detection box
        to the standard YOLO bounding box format: <class_id> <x_center> <y_center> <width> <height>
        """
        class_id = CATEGORY_TO_CLASS_ID.get(box.category, 5)

        w = box.x_max - box.x_min
        h = box.y_max - box.y_min
        x_center = box.x_min + (w / 2.0)
        y_center = box.y_min + (h / 2.0)

        # Clamp values to valid normalized bounds [0.0, 1.0]
        x_c = max(0.0, min(1.0, x_center))
        y_c = max(0.0, min(1.0, y_center))
        w_norm = max(0.0, min(1.0, w))
        h_norm = max(0.0, min(1.0, h))

        return f"{class_id} {x_c:.6f} {y_c:.6f} {w_norm:.6f} {h_norm:.6f}"

    @classmethod
    def detection_to_yolo_seg_line(cls, box: DetectionBox) -> str:
        """
        Converts a polygon mask to YOLO segmentation format:
        <class_id> <x1> <y1> <x2> <y2> ... <xn> <yn>
        Falls back to bounding box corner polygon if no mask polygon is provided.
        """
        class_id = CATEGORY_TO_CLASS_ID.get(box.category, 5)

        if box.mask_polygon and len(box.mask_polygon) >= 3:
            coords = []
            for pt in box.mask_polygon:
                coords.append(f"{pt[0]:.6f} {pt[1]:.6f}")
            return f"{class_id} " + " ".join(coords)

        # Fallback to 4-point bounding box polygon
        p1 = f"{box.x_min:.6f} {box.y_min:.6f}"
        p2 = f"{box.x_max:.6f} {box.y_min:.6f}"
        p3 = f"{box.x_max:.6f} {box.y_max:.6f}"
        p4 = f"{box.x_min:.6f} {box.y_max:.6f}"
        return f"{class_id} {p1} {p2} {p3} {p4}"

    @classmethod
    def parse_yolo_bbox_line(cls, line: str) -> Optional[DetectionBox]:
        """Parses a single YOLO annotation line into a DetectionBox."""
        parts = line.strip().split()
        if len(parts) < 5:
            return None

        try:
            class_id = int(parts[0])
            x_c = float(parts[1])
            y_c = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])

            x_min = max(0.0, x_c - (w / 2.0))
            y_min = max(0.0, y_c - (h / 2.0))
            x_max = min(1.0, x_c + (w / 2.0))
            y_max = min(1.0, y_c + (h / 2.0))

            category = CLASS_ID_TO_CATEGORY.get(class_id, MaterialCategory.MIXED_DEBRIS)

            return DetectionBox(
                x_min=round(x_min, 4),
                y_min=round(y_min, 4),
                x_max=round(x_max, 4),
                y_max=round(y_max, 4),
                confidence=1.0,  # Ground truth label has 100% confidence
                category=category,
                class_id=class_id,
            )
        except Exception as e:
            logger.warning(f"Failed to parse annotation line: {line} ({e})")
            return None

    @classmethod
    def generate_data_yaml(
        cls,
        dataset_dir: str,
        output_yaml_path: Optional[str] = None,
    ) -> str:
        """
        Generates standard Ultralytics YOLO dataset configuration file (data.yaml).
        """
        root = Path(dataset_dir).resolve()
        yaml_content = {
            "path": str(root).replace("\\", "/"),
            "train": "images/train",
            "val": "images/val",
            "test": "images/test" if (root / "images/test").exists() else "images/val",
            "names": {i: name for i, name in enumerate(MATERIAL_CLASS_NAMES)},
            "nc": len(MATERIAL_CLASS_NAMES),
        }

        target_path = Path(output_yaml_path) if output_yaml_path else root / "data.yaml"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w") as f:
            yaml.dump(yaml_content, f, sort_keys=False)

        return str(target_path)

    @classmethod
    def validate_dataset(cls, dataset_dir: str) -> DatasetValidationResult:
        """
        Validates the integrity of a demolition materials dataset:
        - Verifies required directory structure: images/train, labels/train, images/val, labels/val
        - Checks image-to-label pair consistency
        - Verifies normalized coordinate boundaries [0.0, 1.0]
        - Accumulates class distribution histograms
        """
        root = Path(dataset_dir)
        errors: List[str] = []
        warnings: List[str] = []
        class_counts: Dict[str, int] = {name: 0 for name in MATERIAL_CLASS_NAMES}

        train_img_dir = root / "images" / "train"
        train_lbl_dir = root / "labels" / "train"
        val_img_dir = root / "images" / "val"
        val_lbl_dir = root / "labels" / "val"

        if not train_img_dir.exists():
            errors.append(f"Missing training images directory at {train_img_dir}")
        if not train_lbl_dir.exists():
            errors.append(f"Missing training labels directory at {train_lbl_dir}")
        if not val_img_dir.exists():
            warnings.append(f"Validation images directory not found at {val_img_dir}")

        train_count = 0
        val_count = 0

        # Validate training set
        if train_img_dir.exists():
            image_files = [f for f in train_img_dir.glob("*.*") if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
            train_count = len(image_files)

            if train_count == 0:
                warnings.append("Training set has 0 images. Fine-tuning requires labelled images.")

            for img_path in image_files:
                lbl_path = train_lbl_dir / f"{img_path.stem}.txt"
                if not lbl_path.exists():
                    warnings.append(f"Image '{img_path.name}' has no matching label file '{lbl_path.name}'")
                    continue

                with open(lbl_path, "r") as lf:
                    lines = lf.readlines()
                    for line_idx, line in enumerate(lines):
                        parts = line.strip().split()
                        if not parts:
                            continue
                        try:
                            cid = int(parts[0])
                            if 0 <= cid < len(MATERIAL_CLASS_NAMES):
                                class_counts[MATERIAL_CLASS_NAMES[cid]] += 1
                            else:
                                errors.append(f"Invalid class_id {cid} in {lbl_path.name}:{line_idx}")

                            for val in parts[1:5]:
                                coord = float(val)
                                if coord < 0.0 or coord > 1.05:
                                    warnings.append(f"Coordinate {coord} in {lbl_path.name} slightly out of [0, 1]")
                        except ValueError as ve:
                            errors.append(f"Corrupt annotation line in {lbl_path.name}: {ve}")

        # Validate validation set
        if val_img_dir.exists():
            val_image_files = [f for f in val_img_dir.glob("*.*") if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
            val_count = len(val_image_files)

        is_valid = len(errors) == 0 and train_count > 0

        return DatasetValidationResult(
            is_valid=is_valid,
            train_count=train_count,
            val_count=val_count,
            class_distribution=class_counts,
            errors=errors,
            warnings=warnings,
        )

    @classmethod
    def save_human_corrected_annotation(
        cls,
        image_bytes: bytes,
        image_name: str,
        corrected_boxes: List[DetectionBox],
        dataset_base_dir: str = "ai_pipeline/datasets/active_learning",
    ) -> Tuple[str, str]:
        """
        Human-in-the-Loop active learning:
        Persists a verified/corrected demolition site image and its ground-truth annotations
        into the active learning training pool for the next continuous retraining cycle.
        """
        base = Path(dataset_base_dir)
        img_dir = base / "images" / "train"
        lbl_dir = base / "labels" / "train"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        stem = Path(image_name).stem
        ext = Path(image_name).suffix or ".jpg"
        unique_name = f"{stem}_verified_{os.urandom(4).hex()}"

        img_target = img_dir / f"{unique_name}{ext}"
        lbl_target = lbl_dir / f"{unique_name}.txt"

        # Save image
        with open(img_target, "wb") as f:
            f.write(image_bytes)

        # Write YOLO annotation lines
        annotation_lines = []
        for box in corrected_boxes:
            line = cls.detection_to_yolo_bbox_line(box)
            annotation_lines.append(line)

        with open(lbl_target, "w") as f:
            f.write("\n".join(annotation_lines) + "\n")

        # Update data.yaml
        cls.generate_data_yaml(str(base))
        logger.info(f"Saved human-corrected training sample: {img_target.name} with {len(corrected_boxes)} verified boxes.")

        return str(img_target), str(lbl_target)

    @classmethod
    def create_sample_training_dataset(
        cls,
        target_dir: str = "ai_pipeline/datasets/sample_demolition_materials",
        num_train: int = 6,
        num_val: int = 2,
    ) -> str:
        """
        Creates a lightweight valid synthetic dataset representing the 6 demolition material classes
        for automated testing, validation, and dry-run training pipeline execution.
        """
        root = Path(target_dir)
        for split in ("train", "val"):
            (root / "images" / split).mkdir(parents=True, exist_ok=True)
            (root / "labels" / split).mkdir(parents=True, exist_ok=True)

        # Synthetic color palette for classes
        colors = [
            (180, 180, 180),  # 0 concrete (gray)
            (45, 82, 178),    # 1 bricks (red)
            (255, 120, 0),    # 2 steel (blue)
            (42, 100, 150),   # 3 timber (brown)
            (240, 240, 50),   # 4 glass (cyan)
            (100, 100, 100),  # 5 mixed_debris (dark gray)
        ]

        def _generate_synthetic_image_and_label(idx: int, split: str):
            img_bgr = np.full((640, 640, 3), (220, 220, 220), dtype=np.uint8)
            label_lines = []

            # Place 2 material objects per image
            for obj_idx in range(2):
                class_id = (idx * 2 + obj_idx) % len(MATERIAL_CLASS_NAMES)
                color = colors[class_id]

                # Bounding box coordinates
                x1 = 50 + (obj_idx * 280)
                y1 = 80 + (obj_idx * 50)
                x2 = x1 + 220
                y2 = y1 + 240

                cv2.rectangle(img_bgr, (x1, y1), (x2, y2), color, -1)
                cv2.putText(img_bgr, MATERIAL_CLASS_NAMES[class_id], (x1 + 10, y1 + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                # Normalized coordinates
                xc = ((x1 + x2) / 2.0) / 640.0
                yc = ((y1 + y2) / 2.0) / 640.0
                w = (x2 - x1) / 640.0
                h = (y2 - y1) / 640.0

                label_lines.append(f"{class_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")

            img_path = root / "images" / split / f"demo_site_{split}_{idx:03d}.jpg"
            lbl_path = root / "labels" / split / f"demo_site_{split}_{idx:03d}.txt"

            cv2.imwrite(str(img_path), img_bgr)
            with open(lbl_path, "w") as f:
                f.write("\n".join(label_lines) + "\n")

        for i in range(num_train):
            _generate_synthetic_image_and_label(i, "train")

        for i in range(num_val):
            _generate_synthetic_image_and_label(i, "val")

        yaml_path = cls.generate_data_yaml(str(root))
        return yaml_path


dataset_annotator = DemolitionDatasetAnnotator()

