from typing import Dict, List, Optional, Tuple
import numpy as np
from app.core.constants import (
    ConditionGrade,
    MATERIAL_DENSITIES_TONNES_PER_M3,
    MaterialCategory,
)
from ai_pipeline.contracts import (
    BaseConditionClassifier,
    BaseQuantityEstimator,
    ConditionAssessment,
    DetectionBox,
    QuantityEstimate,
)

# Assumed nominal depth/thickness profiles (meters) for 2D visual projections
# Used as baseline when LiDAR or stereoscopic depth points are not supplied
TYPICAL_MATERIAL_DEPTH_METERS: Dict[MaterialCategory, float] = {
    MaterialCategory.CONCRETE: 0.25,     # Typical slab or beam thickness
    MaterialCategory.BRICKS: 0.60,       # Stacked pallet or pile depth
    MaterialCategory.STEEL: 0.30,        # Profile section depth
    MaterialCategory.TIMBER: 0.40,       # Lumber stack thickness
    MaterialCategory.GLASS: 0.05,        # Pane bundle / architectural glass
    MaterialCategory.MIXED_DEBRIS: 0.75, # Rubble heap mound depth
}

# Geometric volumetric packing factor (bulk density ratio vs solid volume)
PACKING_FACTORS: Dict[MaterialCategory, float] = {
    MaterialCategory.CONCRETE: 0.85,
    MaterialCategory.BRICKS: 0.75,
    MaterialCategory.STEEL: 0.50,        # Hollow sections, gaps between beams
    MaterialCategory.TIMBER: 0.70,
    MaterialCategory.GLASS: 0.90,
    MaterialCategory.MIXED_DEBRIS: 0.55, # High void ratio in loose rubble
}


class GeometricQuantityEstimator(BaseQuantityEstimator):
    """
    Calculates physical quantity (volume, mass, surface area) using visual bounding boxes,
    camera calibration/ground sample distance (GSD), and industry bulk density coefficients.
    """

    def estimate(
        self,
        box: DetectionBox,
        image_shape: Tuple[int, int, int],
        camera_height_meters: Optional[float] = None,
        focal_length_mm: Optional[float] = None,
        sensor_width_mm: Optional[float] = None,
        depth_map: Optional[np.ndarray] = None,
    ) -> QuantityEstimate:
        img_h, img_w = image_shape[:2]

        box_w_px = (box.x_max - box.x_min) * img_w
        box_h_px = (box.y_max - box.y_min) * img_h

        # Compute Ground Sample Distance (GSD) in meters/pixel if camera parameters are provided
        # GSD = (Camera Height * Sensor Width) / (Focal Length * Image Width)
        if camera_height_meters and focal_length_mm and sensor_width_mm and focal_length_mm > 0:
            gsd_m_per_px = (camera_height_meters * (sensor_width_mm / 1000.0)) / (
                (focal_length_mm / 1000.0) * img_w
            )
            method = "calibrated_gsd_photogrammetry"
        else:
            # Fallback baseline: assumes standard 1.5m survey distance yielding ~0.002 m/pixel (2mm per pixel)
            gsd_m_per_px = 0.002
            method = "empirical_reference_scale"

        width_m = box_w_px * gsd_m_per_px
        height_m = box_h_px * gsd_m_per_px
        area_m2 = width_m * height_m

        # If a calibrated depth map is available from LiDAR/RGB-D sensors, integrate point cloud depth
        if depth_map is not None:
            y1 = int(box.y_min * img_h)
            y2 = int(box.y_max * img_h)
            x1 = int(box.x_min * img_w)
            x2 = int(box.x_max * img_w)
            depth_crop = depth_map[y1:y2, x1:x2]
            valid_depth = depth_crop[depth_crop > 0]
            depth_m = float(np.median(valid_depth)) if valid_depth.size > 0 else 0.3
            method = "lidar_rgbd_integrated"
        else:
            depth_m = TYPICAL_MATERIAL_DEPTH_METERS.get(box.category, 0.3)

        packing_factor = PACKING_FACTORS.get(box.category, 0.7)
        solid_volume_m3 = round(area_m2 * depth_m * packing_factor, 3)

        # Calculate tonnage using bulk density
        density_t_per_m3 = MATERIAL_DENSITIES_TONNES_PER_M3.get(box.category, 1.5)
        weight_tonnes = round(solid_volume_m3 * density_t_per_m3, 3)

        return QuantityEstimate(
            volume_m3=max(0.01, solid_volume_m3),
            weight_tonnes=max(0.01, weight_tonnes),
            surface_area_m2=round(area_m2, 2),
            unit_count=1 if box.category in (MaterialCategory.STEEL, MaterialCategory.TIMBER) else None,
            estimation_method=method,
        )


class HeuristicConditionAssessor(BaseConditionClassifier):
    """
    Inspects localized material regions for visual degradation indicators,
    mortar adhesion, corrosion/rust discoloration, and fragmentation ratio.
    """

    def assess(
        self,
        crop_bgr: np.ndarray,
        category: MaterialCategory,
    ) -> ConditionAssessment:
        if crop_bgr.size == 0:
            return ConditionAssessment(
                grade=ConditionGrade.RECYCLABLE,
                confidence=0.5,
                hazard_flags=[],
                inspection_notes="Empty image crop. Defaulted to standard recyclable.",
            )

        hazard_flags: List[str] = []
        # Convert to HSV to analyze color saturation and oxidation/corrosion
        hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
        
        # Check for heavy rust/oxidation in steel (orange-red spectrum in HSV)
        if category == MaterialCategory.STEEL:
            lower_rust = np.array([5, 100, 50])
            upper_rust = np.array([25, 255, 200])
            rust_mask = cv2.inRange(hsv, lower_rust, upper_rust)
            rust_ratio = np.sum(rust_mask > 0) / (crop_bgr.shape[0] * crop_bgr.shape[1])
            if rust_ratio > 0.40:
                grade = ConditionGrade.RECYCLABLE
                hazard_flags.append("Heavy surface oxidation / corrosion")
            elif rust_ratio > 0.15:
                grade = ConditionGrade.REUSABLE_GOOD
                hazard_flags.append("Moderate surface rust")
            else:
                grade = ConditionGrade.REUSABLE_EXCELLENT
        
        elif category == MaterialCategory.BRICKS:
            # Check edge roughness / fragmentation using Canny edge variance
            gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (crop_bgr.shape[0] * crop_bgr.shape[1])
            if edge_density > 0.30:
                grade = ConditionGrade.DOWN_CYCLE_ONLY
                hazard_flags.append("High mortar adhesion / fracture fragments")
            else:
                grade = ConditionGrade.REUSABLE_GOOD
        else:
            # Default to standard recyclable pending specialist surveyor verification
            grade = ConditionGrade.RECYCLABLE

        return ConditionAssessment(
            grade=grade,
            confidence=0.75,
            hazard_flags=hazard_flags,
            inspection_notes=f"Automated visual surface inspection completed for {category.value}.",
        )

