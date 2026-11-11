import io
import logging
from typing import List, Tuple
import cv2
import numpy as np
from PIL import Image, ImageOps
from ai_pipeline.contracts import DetectionBox

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Handles image normalization, EXIF orientation correction, tiling, and visual annotations."""

    @staticmethod
    def decode_from_bytes(image_bytes: bytes) -> np.ndarray:
        """
        Safely loads an image from raw bytes, corrects EXIF orientation,
        and converts to an OpenCV BGR numpy array.
        """
        pil_img = Image.open(io.BytesIO(image_bytes))
        # Correct orientation based on EXIF tags (e.g. smartphone or drone rotations)
        pil_img = ImageOps.exif_transpose(pil_img)
        # Convert RGB to BGR for OpenCV
        rgb_array = np.array(pil_img.convert("RGB"))
        bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        return bgr_array

    @staticmethod
    def slice_image_tiles(
        image: np.ndarray,
        tile_size: int = 1280,
        overlap_ratio: float = 0.2,
    ) -> List[Tuple[np.ndarray, int, int]]:
        """
        Slices high-resolution demolition/drone orthophotos into overlapping tiles
        for detecting small material elements without loss of resolution.
        Returns a list of (tile_bgr, x_offset, y_offset).
        """
        h, w = image.shape[:2]
        step = int(tile_size * (1 - overlap_ratio))
        tiles = []

        for y in range(0, max(1, h - tile_size + 1), step):
            for x in range(0, max(1, w - tile_size + 1), step):
                tile = image[y : min(y + tile_size, h), x : min(x + tile_size, w)]
                tiles.append((tile, x, y))

        # Always include at least the resized full frame if smaller than tile_size
        if not tiles:
            tiles.append((image, 0, 0))

        return tiles

    @staticmethod
    def render_bounding_boxes(
        image_bgr: np.ndarray,
        detections: List[DetectionBox],
    ) -> np.ndarray:
        """
        Draws visual annotations (bounding boxes, category tags, confidence scores)
        on an image for inspection.
        """
        canvas = image_bgr.copy()
        h, w = canvas.shape[:2]

        # Category colors (BGR)
        color_map = {
            "CONCRETE": (180, 180, 180),    # Gray
            "BRICKS": (45, 82, 178),        # Brick red
            "STEEL": (255, 120, 0),         # Steel blue
            "TIMBER": (42, 100, 150),       # Timber brown
            "GLASS": (240, 240, 50),        # Cyan glass
            "MIXED_DEBRIS": (100, 100, 100),# Dark gray
        }

        for det in detections:
            x1 = int(det.x_min * w)
            y1 = int(det.y_min * h)
            x2 = int(det.x_max * w)
            y2 = int(det.y_max * h)

            color = color_map.get(det.category.value, (0, 255, 0))
            cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)

            label = f"{det.category.value} {int(det.confidence * 100)}%"
            if det.subcategory:
                label += f" ({det.subcategory})"

            (label_w, label_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                canvas,
                (x1, max(0, y1 - label_h - 6)),
                (x1 + label_w + 4, y1),
                color,
                -1,
            )
            cv2.putText(
                canvas,
                label,
                (x1 + 2, max(label_h, y1 - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        return canvas
