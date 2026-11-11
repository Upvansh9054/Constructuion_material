from typing import Dict, Tuple
from app.core.constants import (
    CARBON_OFFSET_SAVINGS_PER_TONNE,
    ConditionGrade,
    DEFAULT_BASELINE_PRICE_PER_TONNE,
    MATERIAL_DENSITIES_TONNES_PER_M3,
    MaterialCategory,
)

# Valuation multiplier based on material condition
CONDITION_VALUATION_MULTIPLIERS = {
    ConditionGrade.REUSABLE_EXCELLENT: 1.60,  # Premium for direct salvage without reprocessing
    ConditionGrade.REUSABLE_GOOD: 1.15,       # Minor cleaning / sorting needed
    ConditionGrade.RECYCLABLE: 0.85,          # Crushing / remelting grade
    ConditionGrade.DOWN_CYCLE_ONLY: 0.40,     # Aggregate / low-grade backfill
    ConditionGrade.HAZARDOUS_CONTAMINATED: 0.0, # Zero commercial value; requires decontamination
}

# Carbon offset retention multiplier based on reuse vs downcycling
CONDITION_CARBON_MULTIPLIERS = {
    ConditionGrade.REUSABLE_EXCELLENT: 1.20,  # Full displacement of manufacturing & raw extraction
    ConditionGrade.REUSABLE_GOOD: 1.00,
    ConditionGrade.RECYCLABLE: 0.80,          # Reprocessing energy deducted
    ConditionGrade.DOWN_CYCLE_ONLY: 0.35,     # Minimal displacement
    ConditionGrade.HAZARDOUS_CONTAMINATED: 0.0,
}


class MaterialValuationService:
    """Calculates physical weight, commercial secondary recovery value, and circular carbon offsets."""

    @staticmethod
    def calculate_weight_from_volume(
        category: MaterialCategory, volume_m3: float
    ) -> float:
        """Convert volume in m^3 to metric tonnes using material density."""
        density = MATERIAL_DENSITIES_TONNES_PER_M3.get(category, 1.50)
        return round(volume_m3 * density, 3)

    @staticmethod
    def calculate_valuation(
        category: MaterialCategory,
        condition: ConditionGrade,
        weight_tonnes: float,
    ) -> Tuple[float, float]:
        """
        Calculates:
        1. Estimated market recovery value in USD
        2. Embodied carbon emission offset savings in kg CO2e
        """
        if weight_tonnes <= 0:
            return 0.0, 0.0

        base_price_per_tonne = DEFAULT_BASELINE_PRICE_PER_TONNE.get(category, 20.0)
        price_multiplier = CONDITION_VALUATION_MULTIPLIERS.get(condition, 1.0)
        estimated_value = round(base_price_per_tonne * price_multiplier * weight_tonnes, 2)

        base_carbon_factor = CARBON_OFFSET_SAVINGS_PER_TONNE.get(category, 100.0)
        carbon_multiplier = CONDITION_CARBON_MULTIPLIERS.get(condition, 1.0)
        carbon_offset_kg = round(base_carbon_factor * carbon_multiplier * weight_tonnes, 2)

        return estimated_value, carbon_offset_kg


valuation_service = MaterialValuationService()
