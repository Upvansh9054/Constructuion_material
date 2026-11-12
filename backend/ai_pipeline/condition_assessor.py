import logging
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.core.constants import ConditionGrade, MaterialCategory
from ai_pipeline.contracts import ConditionAssessmentExtended

logger = logging.getLogger(__name__)


class MaterialConditionAssessor:
    """
    Computer Vision Material Condition, Damage Severity, and Contamination Assessor.
    Analyzes visible structural defects, oxidation/rusting, fracture edges, and flags
    hazardous materials (Asbestos ACM, Lead Paint, Creosote) for mandatory specialist inspection.
    """

    def assess_crop_condition(
        self,
        crop_bgr: np.ndarray,
        category: MaterialCategory,
        building_year: Optional[int] = None,
        site_has_asbestos_risk: bool = False,
        site_has_lead_paint: bool = False,
        manual_hazard_flags: Optional[List[str]] = None,
    ) -> ConditionAssessmentExtended:
        """
        Executes multi-factor condition analysis on a detected material region.
        """
        if crop_bgr.size == 0 or crop_bgr.shape[0] < 5 or crop_bgr.shape[1] < 5:
            return ConditionAssessmentExtended(
                grade=ConditionGrade.RECYCLABLE,
                damage_severity_pct=25.0,
                damage_type="Uninspected",
                contamination_risk="Pending field survey",
                requires_specialist_abatement=False,
                hazard_inspection_warning=None,
                recommended_recovery_route="CLOSED_LOOP_RECYCLING",
                recoverability_percentage=75.0,
                inspection_notes="Image crop empty or sub-resolution. Defaulted to standard recyclable.",
                confidence=0.50,
                indicators=["Low visual resolution"],
            )

        indicators: List[str] = []
        requires_abatement = False
        hazard_warning = None
        contamination_desc: Optional[str] = None
        damage_type: str = "None"
        damage_severity = 0.0

        h, w = crop_bgr.shape[:2]
        gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)

        # 1. Structural Defect & Edge Degradation
        edges = cv2.Canny(gray, 40, 130)
        edge_density = float(np.sum(edges > 0)) / float(h * w)

        # 2. Material Specific Defect Analysis
        if category == MaterialCategory.STEEL:
            # Analyze Oxidation / Rust in HSV orange-brown spectrum
            lower_rust = np.array([5, 80, 40])
            upper_rust = np.array([28, 255, 210])
            rust_mask = cv2.inRange(hsv, lower_rust, upper_rust)
            rust_ratio = float(np.sum(rust_mask > 0)) / float(h * w)
            damage_severity = round(rust_ratio * 100.0, 1)

            if rust_ratio > 0.45:
                grade = ConditionGrade.RECYCLABLE
                damage_type = "Severe Oxidation & Flake Pitting"
                indicators.append(f"Heavy rust coverage ({damage_severity}%)")
                recoverability = 80.0
                recovery_route = "CLOSED_LOOP_RECYCLING"
            elif rust_ratio > 0.15:
                grade = ConditionGrade.REUSABLE_GOOD
                damage_type = "Moderate Surface Rust"
                indicators.append(f"Light surface rust ({damage_severity}%), profile sound")
                recoverability = 92.0
                recovery_route = "DIRECT_REUSE"
            else:
                grade = ConditionGrade.REUSABLE_EXCELLENT
                damage_type = "Pristine Structural Section"
                indicators.append("Prime condition, no heavy oxidation, straight flanges")
                recoverability = 100.0
                recovery_route = "DIRECT_REUSE"

            # Lead Paint Inspection Rule (Pre-1978 industrial primers)
            if (building_year and building_year < 1978) or site_has_lead_paint:
                requires_abatement = True
                contamination_desc = "Suspected Lead-Based Industrial Primer"
                hazard_warning = (
                    "HAZARD ALERT (EPA/OSHA 29 CFR 1926.62): Pre-1978 steel structural elements "
                    "require lead test prior to mechanical cutting or torching."
                )
                indicators.append("Lead paint risk: historic red-lead primer suspected")

        elif category == MaterialCategory.CONCRETE:
            # Measure surface fracturing and exposed aggregate via edge variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = float(laplacian.var())
            damage_severity = min(100.0, round(variance / 25.0, 1))

            # Look for exposed rust marks from decaying rebar inside concrete
            rebar_stain_mask = cv2.inRange(hsv, np.array([8, 120, 50]), np.array([25, 255, 180]))
            rebar_stain_ratio = float(np.sum(rebar_stain_mask > 0)) / float(h * w)

            if rebar_stain_ratio > 0.08:
                grade = ConditionGrade.DOWN_CYCLE_ONLY
                damage_type = "Rebar Spalling & Internal Carbonation"
                indicators.append("Severe rust bleeding from internal reinforcing mesh")
                recoverability = 55.0
                recovery_route = "DOWNCYCLE_AGGREGATE"
            elif edge_density > 0.28:
                grade = ConditionGrade.RECYCLABLE
                damage_type = "Fractured Demolition Rubble"
                indicators.append(f"High surface fragmentation ({damage_severity}%)")
                recoverability = 85.0
                recovery_route = "CLOSED_LOOP_RECYCLING"
            else:
                grade = ConditionGrade.REUSABLE_GOOD
                damage_type = "Sound Precast / Monolithic Slab"
                indicators.append("Low fracture density, suitable for precast component reuse")
                recoverability = 95.0
                recovery_route = "DIRECT_REUSE"

            # Asbestos Transite / Cement Board Risk
            if site_has_asbestos_risk:
                requires_abatement = True
                grade = ConditionGrade.HAZARDOUS_CONTAMINATED
                contamination_desc = "Asbestos-Containing Material (ACM Transite Sheet)"
                hazard_warning = (
                    "MANDATORY ABATEMENT WARNING (EPA NESHAP 40 CFR Part 61): "
                    "Asbestos cement sheets must NOT be crushed, blended or recycled. "
                    "Licensed hazardous abatement contractor required."
                )
                recoverability = 0.0
                recovery_route = "HAZARDOUS_DISPOSAL"
                indicators.append("CRITICAL: ACM fibers present. Mechanical processing prohibited.")

        elif category == MaterialCategory.BRICKS:
            # Mortar adhesion & chipping analysis
            damage_severity = min(100.0, round(edge_density * 250.0, 1))
            if edge_density > 0.32:
                grade = ConditionGrade.DOWN_CYCLE_ONLY
                damage_type = "Heavy Hard Cement Mortar Adhesion"
                indicators.append("Hard Portland mortar adhered, bricks non-reclaimable intact")
                recoverability = 50.0
                recovery_route = "DOWNCYCLE_AGGREGATE"
            elif edge_density > 0.16:
                grade = ConditionGrade.REUSABLE_GOOD
                damage_type = "Lime Mortar Coated (Cleanable)"
                indicators.append("Lime-based mortar joints, high recovery yield for reclaimed masonry")
                recoverability = 88.0
                recovery_route = "DIRECT_REUSE"
            else:
                grade = ConditionGrade.REUSABLE_EXCELLENT
                damage_type = "Clean Reclaimable Facing Brick"
                indicators.append("Pristine whole facing brick units, zero fracture")
                recoverability = 98.0
                recovery_route = "DIRECT_REUSE"

        elif category == MaterialCategory.TIMBER:
            # Dark discoloration, rot, or charred soot analysis
            dark_mask = cv2.inRange(gray, 0, 45)
            dark_ratio = float(np.sum(dark_mask > 0)) / float(h * w)
            damage_severity = round(dark_ratio * 100.0, 1)

            if dark_ratio > 0.35:
                grade = ConditionGrade.DOWN_CYCLE_ONLY
                damage_type = "Wet Rot / Insect Infestation / Creosote"
                indicators.append(f"Significant timber rot/charring discoloration ({damage_severity}%)")
                recoverability = 40.0
                recovery_route = "DOWNCYCLE_AGGREGATE"
            elif dark_ratio > 0.10:
                grade = ConditionGrade.RECYCLABLE
                damage_type = "Surface Weathering & Nail Holes"
                indicators.append("Sound structural core with superficial weathering")
                recoverability = 85.0
                recovery_route = "CLOSED_LOOP_RECYCLING"
            else:
                grade = ConditionGrade.REUSABLE_EXCELLENT
                damage_type = "Clear Structural Joist / Glulam"
                indicators.append("Dry, uncompromised structural framing lumber")
                recoverability = 98.0
                recovery_route = "DIRECT_REUSE"

        elif category == MaterialCategory.GLASS:
            # Spiderweb cracking / shatter
            damage_severity = min(100.0, round(edge_density * 300.0, 1))
            if edge_density > 0.20:
                grade = ConditionGrade.RECYCLABLE
                damage_type = "Fractured Cullet"
                indicators.append("Fragmented window cullet, suitable for remelting/foam glass")
                recoverability = 80.0
                recovery_route = "CLOSED_LOOP_RECYCLING"
            else:
                grade = ConditionGrade.REUSABLE_GOOD
                damage_type = "Intact Double-Glazed Unit"
                indicators.append("Intact architectural pane, frame salvageable")
                recoverability = 95.0
                recovery_route = "DIRECT_REUSE"

        else:  # MIXED_DEBRIS
            grade = ConditionGrade.DOWN_CYCLE_ONLY
            damage_type = "Unsorted Demolition Rubble"
            damage_severity = 70.0
            indicators.append("Mixed commingled aggregate, requires screening and crushing")
            recoverability = 60.0
            recovery_route = "DOWNCYCLE_AGGREGATE"

        # Apply Global Asbestos Contamination Protocol if site is flagged
        if site_has_asbestos_risk:
            requires_abatement = True
            grade = ConditionGrade.HAZARDOUS_CONTAMINATED
            contamination_desc = "Asbestos-Containing Material (ACM Risk Identified)"
            hazard_warning = (
                "MANDATORY ABATEMENT WARNING (EPA NESHAP 40 CFR Part 61): "
                "Demolition debris containing asbestos must NOT be crushed, blended, or recycled. "
                "Certified hazardous abatement protocol required."
            )
            recoverability = 0.0
            recovery_route = "HAZARDOUS_DISPOSAL"
            indicators.append("CRITICAL: ACM risk flagged for site. Mechanical recycling prohibited under Clean Air Act.")

        # Apply Manual Hazard Flags if provided by surveyor
        if manual_hazard_flags:
            for flag in manual_hazard_flags:
                indicators.append(f"Surveyor flagged: {flag}")
                if "asbestos" in flag.lower():
                    requires_abatement = True
                    grade = ConditionGrade.HAZARDOUS_CONTAMINATED
                    contamination_desc = "Confirmed Asbestos-Containing Material"
                    hazard_warning = "MANDATORY HAZARDOUS DISPOSAL: Certified abatement protocol active."
                    recoverability = 0.0
                    recovery_route = "HAZARDOUS_DISPOSAL"
                elif "lead" in flag.lower():
                    requires_abatement = True
                    contamination_desc = "Confirmed Lead Contamination"

        notes = (
            f"Automated condition assessment completed for {category.value}. "
            f"Damage severity: {damage_severity}%. Recommended route: {recovery_route}."
        )

        return ConditionAssessmentExtended(
            grade=grade,
            damage_severity_pct=damage_severity,
            damage_type=damage_type,
            contamination_risk=contamination_desc,
            requires_specialist_abatement=requires_abatement,
            hazard_inspection_warning=hazard_warning,
            recommended_recovery_route=recovery_route,
            recoverability_percentage=recoverability,
            inspection_notes=notes,
            confidence=0.86,
            indicators=indicators,
        )


condition_assessor_extended = MaterialConditionAssessor()
