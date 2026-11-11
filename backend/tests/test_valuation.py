import pytest
from app.core.constants import ConditionGrade, MaterialCategory
from app.services.valuation import valuation_service


def test_calculate_weight_from_volume():
    # Steel density = 7.85 t/m^3
    weight_steel = valuation_service.calculate_weight_from_volume(
        category=MaterialCategory.STEEL,
        volume_m3=10.0,
        packing_factor=1.0,
    )
    assert weight_steel == 78.5

    # Concrete density = 2.40 t/m^3 with packing factor 0.85
    weight_concrete = valuation_service.calculate_weight_from_volume(
        category=MaterialCategory.CONCRETE,
        volume_m3=100.0,
        packing_factor=0.85,
    )
    assert weight_concrete == 204.0


def test_valuation_condition_multipliers():
    # Structural steel baseline price = $320 / tonne, multiplier = 1.60
    val_excellent, carbon_excellent = valuation_service.calculate_valuation(
        category=MaterialCategory.STEEL,
        condition=ConditionGrade.REUSABLE_EXCELLENT,
        weight_tonnes=10.0,
    )
    assert val_excellent == 5120.0
    assert carbon_excellent == 21600.0

    # DOWN_CYCLE_ONLY has multiplier 0.40, carbon multiplier 0.35
    val_downcycle, carbon_downcycle = valuation_service.calculate_valuation(
        category=MaterialCategory.STEEL,
        condition=ConditionGrade.DOWN_CYCLE_ONLY,
        weight_tonnes=10.0,
    )
    assert val_downcycle == 1280.0
    assert carbon_downcycle == 6300.0


def test_zero_tonnes_valuation():
    val, carbon = valuation_service.calculate_valuation(
        category=MaterialCategory.TIMBER,
        condition=ConditionGrade.RECYCLABLE,
        weight_tonnes=0.0,
    )
    assert val == 0.0
    assert carbon == 0.0
