import numpy as np
import pytest
from ai_pipeline.contracts import DetectionBox
from ai_pipeline.detector import ModelWeightsNotFoundError, YOLOMaterialDetector
from ai_pipeline.estimator import GeometricQuantityEstimator
from ai_pipeline.preprocessor import ImagePreprocessor
from app.core.constants import MaterialCategory


def test_image_preprocessor_tiling():
    # Test tile generation from high-res image
    dummy_img = np.zeros((1500, 2000, 3), dtype=np.uint8)
    tiles = ImagePreprocessor.slice_image_tiles(dummy_img, tile_size=1000, overlap_ratio=0.2)

    assert len(tiles) > 1
    tile, x, y = tiles[0]
    assert tile.shape[0] <= 1000
    assert tile.shape[1] <= 1000


def test_detector_missing_weights_raises_error():
    """Verify strictly that the AI detector never presents fake results without real weights."""
    detector = YOLOMaterialDetector(weights_path="non_existent_weights_2026.pt")
    dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)

    with pytest.raises(ModelWeightsNotFoundError):
        detector.detect(dummy_img)


def test_geometric_quantity_estimator():
    estimator = GeometricQuantityEstimator()
    box = DetectionBox(
        x_min=0.1,
        y_min=0.1,
        x_max=0.6,
        y_max=0.5,
        confidence=0.92,
        category=MaterialCategory.CONCRETE,
    )
    # 4000x3000 image, 45m camera altitude, 24mm focal length, 13.2mm sensor width
    result = estimator.estimate(
        box=box,
        image_shape=(3000, 4000, 3),
        camera_height_meters=45.0,
        focal_length_mm=24.0,
        sensor_width_mm=13.2,
    )

    assert result.volume_m3 > 0.0
    assert result.weight_tonnes > 0.0
    assert result.surface_area_m2 is not None
    assert result.estimation_method == "calibrated_gsd_photogrammetry"
