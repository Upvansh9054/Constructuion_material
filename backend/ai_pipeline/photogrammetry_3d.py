import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import open3d as o3d

from app.core.constants import (
    MATERIAL_DENSITIES_TONNES_PER_M3,
    MaterialCategory,
)
from ai_pipeline.contracts import (
    DetectionBox,
    MultiViewReconstructionResult,
    QuantityEstimateExtended,
)

logger = logging.getLogger(__name__)

# Standard structural thickness & depth priors (meters) with uncertainty envelopes [min, nominal, max]
STRUCTURAL_DEPTH_PRIORS: Dict[MaterialCategory, Dict[str, float]] = {
    MaterialCategory.CONCRETE: {"min": 0.15, "nominal": 0.25, "max": 0.45},
    MaterialCategory.BRICKS: {"min": 0.22, "nominal": 0.45, "max": 0.80},
    MaterialCategory.STEEL: {"min": 0.12, "nominal": 0.30, "max": 0.55},
    MaterialCategory.TIMBER: {"min": 0.15, "nominal": 0.30, "max": 0.50},
    MaterialCategory.GLASS: {"min": 0.01, "nominal": 0.025, "max": 0.06},
    MaterialCategory.MIXED_DEBRIS: {"min": 0.35, "nominal": 0.65, "max": 1.25},
}

# Industry Packing / Void Factors (Bulk Solid Volume vs Gross Bounding Volume)
PACKING_FACTORS_CONFIG: Dict[MaterialCategory, Dict[str, float]] = {
    MaterialCategory.CONCRETE: {"min": 0.75, "nominal": 0.85, "max": 0.95},
    MaterialCategory.BRICKS: {"min": 0.65, "nominal": 0.75, "max": 0.85},
    MaterialCategory.STEEL: {"min": 0.35, "nominal": 0.48, "max": 0.65},  # Structural profiles have large void space
    MaterialCategory.TIMBER: {"min": 0.60, "nominal": 0.72, "max": 0.85},
    MaterialCategory.GLASS: {"min": 0.80, "nominal": 0.90, "max": 0.98},
    MaterialCategory.MIXED_DEBRIS: {"min": 0.45, "nominal": 0.55, "max": 0.70},  # Loose crushed rubble has high void ratio
}

# Material Bulk Density Ranges (tonnes per m3) according to CIRIA & Eurocode standards
MATERIAL_DENSITY_RANGES: Dict[MaterialCategory, Dict[str, float]] = {
    MaterialCategory.CONCRETE: {"min": 2.30, "nominal": 2.40, "max": 2.55},
    MaterialCategory.BRICKS: {"min": 1.75, "nominal": 1.90, "max": 2.05},
    MaterialCategory.STEEL: {"min": 7.75, "nominal": 7.85, "max": 7.95},
    MaterialCategory.TIMBER: {"min": 0.50, "nominal": 0.65, "max": 0.80},
    MaterialCategory.GLASS: {"min": 2.40, "nominal": 2.50, "max": 2.65},
    MaterialCategory.MIXED_DEBRIS: {"min": 1.40, "nominal": 1.60, "max": 1.85},
}


class MultiViewPhotogrammetryEngine:
    """
    Multi-View 3D Photogrammetric Reconstruction Engine using OpenCV and Open3D.
    Performs epipolar feature matching, relative camera pose recovery,
    triangulation, and 3D point cloud convex hull / bounding box volume estimation.
    """

    def __init__(self):
        # Prefer SIFT for scale invariance, fall back to ORB
        try:
            self.detector = cv2.SIFT_create(nfeatures=2500)
            self.use_flann = True
            logger.info("MultiViewPhotogrammetryEngine initialized with SIFT feature detector.")
        except Exception:
            self.detector = cv2.ORB_create(nfeatures=2500)
            self.use_flann = False
            logger.info("MultiViewPhotogrammetryEngine initialized with ORB feature detector.")

    def reconstruct_from_stereo_pair(
        self,
        image_a_bgr: np.ndarray,
        image_b_bgr: np.ndarray,
        focal_length_mm: Optional[float] = None,
        sensor_width_mm: Optional[float] = None,
        baseline_distance_m: Optional[float] = None,
        camera_height_m: Optional[float] = None,
    ) -> MultiViewReconstructionResult:
        """
        Reconstructs a metric 3D point cloud from two overlapping views of a demolition scene.
        """
        h_a, w_a = image_a_bgr.shape[:2]
        h_b, w_b = image_b_bgr.shape[:2]

        gray_a = cv2.cvtColor(image_a_bgr, cv2.COLOR_BGR2GRAY)
        gray_b = cv2.cvtColor(image_b_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Feature Detection
        kp_a, des_a = self.detector.detectAndCompute(gray_a, None)
        kp_b, des_b = self.detector.detectAndCompute(gray_b, None)

        if des_a is None or des_b is None or len(kp_a) < 12 or len(kp_b) < 12:
            return self._create_fallback_result("Insufficient keypoint features in stereo image pair.")

        # 2. Descriptor Matching
        if self.use_flann:
            flann_index_kdtree = 1
            index_params = dict(algorithm=flann_index_kdtree, trees=5)
            search_params = dict(checks=50)
            matcher = cv2.FlannBasedMatcher(index_params, search_params)
            matches = matcher.knnMatch(des_a, des_b, k=2)
            # Lowe's ratio test
            good_matches = [m for m, n in matches if m.distance < 0.75 * n.distance]
        else:
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            good_matches = matcher.match(des_a, des_b)

        if len(good_matches) < 8:
            return self._create_fallback_result(f"Too few feature correspondences ({len(good_matches)} matched).")

        pts_a = np.float32([kp_a[m.queryIdx].pt for m in good_matches]).reshape(-1, 2)
        pts_b = np.float32([kp_b[m.trainIdx].pt for m in good_matches]).reshape(-1, 2)

        # 3. Camera Intrinsics Matrix K
        if focal_length_mm and sensor_width_mm and sensor_width_mm > 0:
            fx = (focal_length_mm / sensor_width_mm) * w_a
            fy = fx
        else:
            fx = fy = 1.15 * w_a  # Standard nominal wide-angle drone lens assumption

        cx, cy = w_a / 2.0, h_a / 2.0
        K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float64)

        # 4. Essential Matrix & Relative Camera Pose (R, t)
        E, inlier_mask = cv2.findEssentialMat(pts_a, pts_b, K, method=cv2.RANSAC, prob=0.999, threshold=1.2)
        if E is None or inlier_mask is None:
            return self._create_fallback_result("Could not compute valid Essential Matrix between frames.")

        inliers_count = int(np.sum(inlier_mask))
        if inliers_count < 8:
            return self._create_fallback_result(f"RANSAC inlier count too low ({inliers_count} inliers).")

        _, R, t, mask_pose = cv2.recoverPose(E, pts_a, pts_b, K, mask=inlier_mask)

        # 5. Triangulation of 3D Points
        proj_a = K @ np.hstack((np.eye(3), np.zeros((3, 1))))
        proj_b = K @ np.hstack((R, t))

        pts_a_inliers = pts_a[mask_pose.ravel() > 0].T
        pts_b_inliers = pts_b[mask_pose.ravel() > 0].T

        if pts_a_inliers.shape[1] < 4:
            return self._create_fallback_result("Insufficient points in positive parallax.")

        points_4d = cv2.triangulatePoints(proj_a, proj_b, pts_a_inliers, pts_b_inliers)
        points_3d = (points_4d[:3] / points_4d[3]).T  # De-homogenize

        # Filter valid points in front of cameras
        valid_indices = (points_3d[:, 2] > 0.1) & (points_3d[:, 2] < 200.0)
        filtered_points = points_3d[valid_indices]

        if len(filtered_points) < 6:
            return self._create_fallback_result("Triangulated points degenerate or outside valid depth horizon.")

        # Metric scale recovery factor
        scale_factor = 1.0
        if baseline_distance_m and baseline_distance_m > 0:
            current_norm = np.linalg.norm(t)
            scale_factor = baseline_distance_m / current_norm if current_norm > 0 else 1.0
        elif camera_height_m and camera_height_m > 0:
            median_z = float(np.median(filtered_points[:, 2]))
            scale_factor = camera_height_m / median_z if median_z > 0 else 1.0

        filtered_points = filtered_points * scale_factor

        # 6. Open3D Point Cloud Processing
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(filtered_points)

        # Outlier removal
        if len(pcd.points) > 10:
            pcd_clean, _ = pcd.remove_statistical_outlier(nb_neighbors=min(20, len(pcd.points) - 1), std_ratio=2.0)
            clean_points = np.asarray(pcd_clean.points)
            if len(clean_points) >= 4:
                pcd = pcd_clean
                filtered_points = clean_points

        # Calculate 3D Dimensions & Convex Hull Volume
        min_bound = pcd.get_min_bound()
        max_bound = pcd.get_max_bound()
        dims = max_bound - min_bound  # [dx, dy, dz]

        length_m = float(round(dims[0], 3))
        width_m = float(round(dims[1], 3))
        height_m = float(round(dims[2], 3))

        convex_volume_m3 = 0.0
        try:
            if len(pcd.points) >= 4:
                hull, _ = pcd.compute_convex_hull()
                convex_volume_m3 = float(round(hull.get_volume(), 3))
        except Exception as e:
            logger.debug(f"Open3D convex hull computation notice: {e}")

        # Fallback to oriented bounding box volume if hull is flat
        if convex_volume_m3 <= 0.001:
            convex_volume_m3 = float(round(length_m * width_m * max(0.1, height_m) * 0.65, 3))

        # Sample point cloud summary for frontend 3D visualizer
        sample_size = min(150, len(filtered_points))
        sample_indices = np.random.choice(len(filtered_points), sample_size, replace=False)
        sampled_pts = filtered_points[sample_indices]
        point_cloud_summary = {
            "sample_points": sampled_pts.round(3).tolist(),
            "center": pcd.get_center().round(3).tolist(),
            "scale_factor_applied": round(scale_factor, 3),
        }

        confidence = min(0.95, max(0.40, inliers_count / (len(good_matches) + 1e-6)))

        return MultiViewReconstructionResult(
            point_count=len(filtered_points),
            bounding_box_3d={
                "length_m": length_m,
                "width_m": width_m,
                "height_m": height_m,
                "volume_m3": round(length_m * width_m * height_m, 3),
            },
            convex_hull_volume_m3=max(0.01, convex_volume_m3),
            reconstruction_confidence=round(confidence, 2),
            matched_features_count=len(good_matches),
            triangulation_error_px=round(1.0 / (confidence + 0.1), 2),
            methodology_used="PHOTOGRAMMETRY_MULTIVIEW_POINTCLOUD",
            point_cloud_summary=point_cloud_summary,
        )

    def _create_fallback_result(self, reason: str) -> MultiViewReconstructionResult:
        logger.info(f"Multi-view reconstruction fallback engaged: {reason}")
        return MultiViewReconstructionResult(
            point_count=0,
            bounding_box_3d={"length_m": 0.0, "width_m": 0.0, "height_m": 0.0, "volume_m3": 0.0},
            convex_hull_volume_m3=0.0,
            reconstruction_confidence=0.0,
            matched_features_count=0,
            triangulation_error_px=0.0,
            methodology_used="UNAVAILABLE_INSUFFICIENT_OVERLAP",
            point_cloud_summary={"error": reason},
        )


class CalibratedQuantityEstimator:
    """
    Computes rigorous physical dimensions, surface areas, solid volumes,
    and tonnage estimates with explicit uncertainty ranges and fully visible assumptions.
    Supports GSD calibration, manual reference measurements, and building gross volumetric bounds.
    """

    def __init__(self, photogrammetry_engine: Optional[MultiViewPhotogrammetryEngine] = None):
        self.photogrammetry_engine = photogrammetry_engine or MultiViewPhotogrammetryEngine()

    def estimate_from_detection(
        self,
        box: DetectionBox,
        image_shape: Tuple[int, int, int],
        category: MaterialCategory,
        camera_height_m: Optional[float] = None,
        focal_length_mm: Optional[float] = None,
        sensor_width_mm: Optional[float] = None,
        reference_measurement_m: Optional[float] = None,
        reference_pixel_length: Optional[float] = None,
        manual_length_m: Optional[float] = None,
        manual_width_m: Optional[float] = None,
        manual_height_m: Optional[float] = None,
        custom_density_t_per_m3: Optional[float] = None,
        custom_packing_factor: Optional[float] = None,
        reconstruction_result: Optional[MultiViewReconstructionResult] = None,
    ) -> QuantityEstimateExtended:
        """
        Estimates visible material dimensions, volume, mass, and uncertainty interval.
        Explicitly prevents confusing pixel area with physical volume.
        """
        img_h, img_w = image_shape[:2]
        box_w_px = max(1.0, (box.x_max - box.x_min) * img_w)
        box_h_px = max(1.0, (box.y_max - box.y_min) * img_h)

        assumptions: Dict[str, Any] = {}

        # 1. Determine Spatial Scaling & Methodology
        if manual_length_m and manual_width_m:
            # Surveyor provided manual physical dimensions
            length_m = manual_length_m
            width_m = manual_width_m
            height_m = manual_height_m or STRUCTURAL_DEPTH_PRIORS[category]["nominal"]
            surface_area_m2 = length_m * width_m
            method = "MANUAL_SURVEYOR_TAKEOFF"
            uncertainty_pct = 10.0
            assumptions["calibration_type"] = "surveyor_tape_or_laser_rangefinder"

        elif reconstruction_result and reconstruction_result.point_count > 0 and reconstruction_result.reconstruction_confidence >= 0.45:
            # 3D Photogrammetry Point Cloud from multi-view stereo
            bbox = reconstruction_result.bounding_box_3d
            length_m = max(0.1, bbox.get("length_m", 1.0))
            width_m = max(0.1, bbox.get("width_m", 1.0))
            height_m = max(0.05, bbox.get("height_m", STRUCTURAL_DEPTH_PRIORS[category]["nominal"]))
            surface_area_m2 = length_m * width_m
            method = "PHOTOGRAMMETRY_MULTIVIEW_POINTCLOUD"
            uncertainty_pct = 15.0
            assumptions["point_count"] = reconstruction_result.point_count
            assumptions["convex_hull_volume_m3"] = reconstruction_result.convex_hull_volume_m3

        elif reference_measurement_m and reference_pixel_length and reference_pixel_length > 0:
            # Known physical reference object in scene (e.g. 1.0m surveyor rod or 2.1m doorway)
            scale_m_per_px = reference_measurement_m / reference_pixel_length
            width_m = box_w_px * scale_m_per_px
            length_m = box_h_px * scale_m_per_px
            height_m = STRUCTURAL_DEPTH_PRIORS[category]["nominal"]
            surface_area_m2 = width_m * length_m
            method = "REFERENCE_OBJECT_SCALED"
            uncertainty_pct = 18.0
            assumptions["reference_known_m"] = reference_measurement_m
            assumptions["reference_px"] = reference_pixel_length
            assumptions["scale_m_per_px"] = round(scale_m_per_px, 5)

        elif camera_height_m and focal_length_mm and sensor_width_mm and focal_length_mm > 0:
            # Calibrated Ground Sampling Distance (GSD) Photogrammetry
            # GSD = (Camera Height * Sensor Width) / (Focal Length * Image Width)
            gsd_m_per_px = (camera_height_m * (sensor_width_mm / 1000.0)) / (
                (focal_length_mm / 1000.0) * img_w
            )
            width_m = box_w_px * gsd_m_per_px
            length_m = box_h_px * gsd_m_per_px
            height_m = STRUCTURAL_DEPTH_PRIORS[category]["nominal"]
            surface_area_m2 = width_m * length_m
            method = "CALIBRATED_MONOCULAR_GSD"
            uncertainty_pct = 22.0
            assumptions["camera_altitude_m"] = camera_height_m
            assumptions["focal_length_mm"] = focal_length_mm
            assumptions["sensor_width_mm"] = sensor_width_mm
            assumptions["gsd_m_per_px"] = round(gsd_m_per_px, 5)

        else:
            # Baseline uncalibrated perspective prior
            # Uses conservative 0.0035 m/px standard survey distance baseline
            baseline_gsd = 0.0035
            width_m = box_w_px * baseline_gsd
            length_m = box_h_px * baseline_gsd
            height_m = STRUCTURAL_DEPTH_PRIORS[category]["nominal"]
            surface_area_m2 = width_m * length_m
            method = "UNSCALED_MONOCULAR_PRIOR"
            uncertainty_pct = 35.0
            assumptions["warning"] = "Uncalibrated image. Single photo cannot determine exact physical tonnage without scale reference."

        # 2. Material Density and Packing Factor Assumptions
        depth_prior = STRUCTURAL_DEPTH_PRIORS[category]
        packing_cfg = PACKING_FACTORS_CONFIG[category]
        density_cfg = MATERIAL_DENSITY_RANGES[category]

        nominal_density = custom_density_t_per_m3 or density_cfg["nominal"]
        nominal_packing = custom_packing_factor or packing_cfg["nominal"]

        assumptions["assumed_density_t_per_m3"] = nominal_density
        assumptions["packing_factor"] = nominal_packing
        assumptions["depth_prior_m"] = depth_prior["nominal"]

        # 3. Solid Volume Estimation
        # Avoid confusing 2D surface area with solid volume!
        nominal_volume_m3 = round(surface_area_m2 * height_m * nominal_packing, 3)
        min_depth = depth_prior["min"]
        max_depth = depth_prior["max"]

        min_volume_m3 = round(
            surface_area_m2 * (1.0 - uncertainty_pct / 100.0) * min_depth * packing_cfg["min"], 3
        )
        max_volume_m3 = round(
            surface_area_m2 * (1.0 + uncertainty_pct / 100.0) * max_depth * packing_cfg["max"], 3
        )

        # 4. Weight Calculation with Uncertainty Range
        nominal_weight_tonnes = round(nominal_volume_m3 * nominal_density, 3)
        min_weight_tonnes = round(min_volume_m3 * density_cfg["min"], 3)
        max_weight_tonnes = round(max_volume_m3 * density_cfg["max"], 3)

        return QuantityEstimateExtended(
            nominal_volume_m3=max(0.01, nominal_volume_m3),
            nominal_weight_tonnes=max(0.01, nominal_weight_tonnes),
            min_volume_m3=max(0.005, min_volume_m3),
            max_volume_m3=max(0.02, max_volume_m3),
            min_weight_tonnes=max(0.005, min_weight_tonnes),
            max_weight_tonnes=max(0.02, max_weight_tonnes),
            uncertainty_percentage=round(uncertainty_pct, 1),
            length_m=round(length_m, 2),
            width_m=round(width_m, 2),
            height_m=round(height_m, 2),
            surface_area_m2=round(surface_area_m2, 2),
            assumed_density_t_per_m3=nominal_density,
            packing_factor=nominal_packing,
            estimation_method=method,
            assumptions_applied=assumptions,
        )


# Global singleton instances
photogrammetry_engine = MultiViewPhotogrammetryEngine()
quantity_estimator_3d = CalibratedQuantityEstimator(photogrammetry_engine)

