import pytest
import asyncio
from backend.app.schemas.fertilizer import SoilTestInput
from backend.app.services.fertilizer_service import fertilizer_service

@pytest.mark.asyncio
async def test_coffee_fertilizer_workflow():
    """
    Test Case 1: Coffee in Coorg, Karnataka.
    2.5 acres, yielding adult bearing bushes.
    Soil test: N = 180 kg/ha (Low), P = 15 kg/ha (Medium), K = 120 kg/ha (Medium).
    Manure: 5 tons/ha FYM applied.
    """
    inp = SoilTestInput(
        crop="coffee",
        growth_stage="bearing",
        location="Coorg, Karnataka",
        field_area=2.5,
        area_unit="acres",
        soil_n=180.0,
        soil_p=15.0,
        soil_k=120.0,
        nutrient_unit="kg/ha",
        soil_ph=6.2,
        organic_carbon_percent=0.65,
        fym_applied_tons_per_ha=5.0
    )
    res = await fertilizer_service.get_recommendation(inp)
    
    # Assertions on conversions
    assert res.crop == "coffee"
    assert round(res.area_summary["area_in_acres"], 1) == 2.5
    assert res.area_summary["area_in_hectares"] > 1.0 # 2.5 acres ~ 1.01 ha
    
    # Assertions on soil ratings
    assert res.soil_test_rating["N"] == "Low"
    assert res.soil_test_rating["P"] == "Medium"
    assert res.soil_test_rating["K"] == "Medium"
    
    # Manure credit deduction check
    assert res.manure_credits_deducted_kg_per_ha["N"] == 7.5 # 5 * 1.5
    assert res.manure_credits_deducted_kg_per_ha["P2O5"] == 6.0 # 5 * 1.2
    assert res.manure_credits_deducted_kg_per_ha["K2O"] == 17.5 # 5 * 3.5
    
    # Commercial products check: DAP, Urea, MOP present
    prod_names = [p.product_name for p in res.commercial_fertilizers]
    assert any("DAP" in p for p in prod_names)
    assert any("Urea" in p for p in prod_names)
    assert any("MOP" in p for p in prod_names)
    
    # Split schedule check: 3 splits for coffee (Pre-Monsoon, Mid-Monsoon, Post-Monsoon)
    assert len(res.split_schedule) == 3
    
    # Weather and citation check
    assert res.weather_adjustment is not None
    assert len(res.citations) > 0


@pytest.mark.asyncio
async def test_potato_fertilizer_workflow():
    """
    Test Case 2: Potato in Hassan, Karnataka.
    1.0 hectare.
    Soil test: N = 220 kg/ha (Low), P = 25 kg/ha (Medium), K = 160 kg/ha (Medium).
    No FYM applied.
    """
    inp = SoilTestInput(
        crop="potato",
        growth_stage="tuber_production",
        location="Hassan, Karnataka",
        field_area=1.0,
        area_unit="hectares",
        soil_n=220.0,
        soil_p=25.0,
        soil_k=160.0,
        nutrient_unit="kg/ha",
        soil_ph=5.4 # Strongly acidic, should trigger liming alert
    )
    res = await fertilizer_service.get_recommendation(inp)
    
    assert res.crop == "potato"
    assert res.soil_test_rating["N"] == "Low" # < 250
    # Acidic pH should produce a safety warning
    assert any("acidic" in w.lower() for w in res.safety_warnings)
    # Split schedule: Basal + Top Dressing at earthing up
    assert len(res.split_schedule) == 2


@pytest.mark.asyncio
async def test_maize_unit_conversion_and_guntas():
    """
    Test Case 3: Maize in Karnataka, measured in 40 Guntas (= 1 acre).
    Units in ppm: N = 80 ppm (~179 kg/ha), P = 8 ppm (~18 kg/ha), K = 60 ppm (~134 kg/ha).
    """
    inp = SoilTestInput(
        crop="maize",
        growth_stage="hybrid",
        location="Dharwad, Karnataka",
        field_area=40.0,
        area_unit="guntas",
        soil_n=80.0,
        soil_p=8.0,
        soil_k=60.0,
        nutrient_unit="ppm"
    )
    res = await fertilizer_service.get_recommendation(inp)
    
    # 40 guntas must convert to approx 1 acre (0.404686 ha)
    assert round(res.area_summary["area_in_acres"], 1) == 1.0
    assert len(res.split_schedule) == 3 # Basal, Knee-High, Tasseling
    # Check that DAP N deduction prevents double counting
    dap_prod = next(p for p in res.commercial_fertilizers if "DAP" in p.product_name)
    urea_prod = next(p for p in res.commercial_fertilizers if "Urea" in p.product_name)
    assert "accounting for" in urea_prod.purpose.lower()
