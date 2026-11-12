import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from backend.app.schemas.fertilizer import (
    SoilTestInput,
    FertilizerRecommendationResponse,
    FertilizerProductDose,
    SplitScheduleItem,
    WeatherAdjustment,
    OrganicAlternative
)
from backend.app.services.weather_service import weather_service

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

class FertilizerService:
    def __init__(self):
        rules_path = DATA_DIR / "agronomy_rules.json"
        with open(rules_path, "r", encoding="utf-8") as f:
            self.rules = json.load(f)

    def convert_area_to_hectares(self, area: float, unit: str) -> float:
        """Convert any regional land area unit to metric hectares."""
        u = unit.strip().lower()
        if u in ("hectares", "hectare", "ha"):
            return area
        elif u in ("acres", "acre"):
            return area * 0.404686
        elif u in ("guntas", "guntha"):
            # 40 guntas = 1 acre
            return (area / 40.0) * 0.404686
        elif u in ("bighas", "bigha"):
            # Standard pucca bigha = 0.2529 ha (approx 1.6 bigha per acre)
            return area * 0.252928
        elif u in ("cents", "cent"):
            # 100 cents = 1 acre
            return (area / 100.0) * 0.404686
        else:
            raise ValueError(f"Unsupported area unit: {unit}")

    def normalize_soil_nutrients(self, n: float, p: float, k: float, unit: str) -> Tuple[float, float, float]:
        """Normalize soil test values to standard kg/ha."""
        u = unit.strip().lower()
        if u == "kg/ha":
            return n, p, k
        elif u in ("ppm", "mg/kg"):
            # 1 ppm in plow layer (15 cm, BD 1.33) ~ 2.24 kg/ha
            return n * 2.24, p * 2.24, k * 2.24
        elif u in ("lb/acre", "lbs/acre"):
            # 1 lb/acre ~ 1.12085 kg/ha
            return n * 1.12085, p * 1.12085, k * 1.12085
        else:
            raise ValueError(f"Unsupported nutrient unit: {unit}")

    def classify_nutrient_rating(self, crop: str, n_kg_ha: float, p_kg_ha: float, k_kg_ha: float) -> Tuple[Dict[str, str], Dict[str, float]]:
        """Classify soil test values into Low, Medium, High and compute adjustment factors."""
        thresholds = self.rules[crop]["soil_rating_thresholds_kg_per_ha"]
        
        ratings = {}
        factors = {}
        
        # Nitrogen
        n_thresh = thresholds["N"]
        if n_kg_ha < n_thresh["low"]:
            ratings["N"] = "Low"
            factors["N"] = 1.25 # +25%
        elif n_kg_ha <= n_thresh["medium_max"]:
            ratings["N"] = "Medium"
            factors["N"] = 1.0 # 100% recommended dose
        else:
            ratings["N"] = "High"
            factors["N"] = 0.75 # -25%
            
        # Phosphorus
        p_thresh = thresholds["P"]
        if p_kg_ha < p_thresh["low"]:
            ratings["P"] = "Low"
            factors["P"] = 1.25
        elif p_kg_ha <= p_thresh["medium_max"]:
            ratings["P"] = "Medium"
            factors["P"] = 1.0
        else:
            ratings["P"] = "High"
            factors["P"] = 0.75
            
        # Potassium
        k_thresh = thresholds["K"]
        if k_kg_ha < k_thresh["low"]:
            ratings["K"] = "Low"
            factors["K"] = 1.25
        elif k_kg_ha <= k_thresh["medium_max"]:
            ratings["K"] = "Medium"
            factors["K"] = 1.0
        else:
            ratings["K"] = "High"
            factors["K"] = 0.75
            
        return ratings, factors

    def calculate_manure_credits(self, fym_tons_per_ha: float) -> Dict[str, float]:
        """
        Calculate available nutrient credit from Farmyard Manure (FYM).
        1 ton FYM contains ~0.5% N, 0.2% P2O5, 0.5% K2O.
        First year mineralized availability: N 30%, P 60%, K 70%.
        Credit per ton: N = 1.5 kg, P2O5 = 1.2 kg, K2O = 3.5 kg.
        """
        if not fym_tons_per_ha or fym_tons_per_ha <= 0:
            return {"N": 0.0, "P2O5": 0.0, "K2O": 0.0}
            
        return {
            "N": round(fym_tons_per_ha * 1.5, 1),
            "P2O5": round(fym_tons_per_ha * 1.2, 1),
            "K2O": round(fym_tons_per_ha * 3.5, 1)
        }

    def solve_commercial_fertilizers(
        self,
        net_n: float,
        net_p2o5: float,
        net_k2o: float,
        area_ha: float,
        area_acres: float
    ) -> List[FertilizerProductDose]:
        """
        Solve commercial fertilizer quantities WITHOUT double-counting nutrients.
        DAP (18% N, 46% P2O5) supplies P2O5, and its N is deducted from Urea (46% N).
        MOP (60% K2O) supplies K2O.
        """
        products = []
        
        # 1. Phosphorus satisfied by DAP
        dap_per_ha = 0.0
        n_supplied_by_dap = 0.0
        if net_p2o5 > 0:
            dap_per_ha = net_p2o5 / 0.46
            n_supplied_by_dap = dap_per_ha * 0.18
            dap_total = dap_per_ha * area_ha
            dap_per_acre = dap_per_ha / 2.47105
            products.append(FertilizerProductDose(
                product_name="DAP (Di-Ammonium Phosphate)",
                nutrient_composition="18-46-0",
                amount_per_ha_kg=round(dap_per_ha, 1),
                amount_per_acre_kg=round(dap_per_acre, 1),
                total_field_kg=round(dap_total, 1),
                bags_50kg_needed=round(dap_total / 50.0, 1),
                application_method="Basal placement in soil",
                timing="At planting/sowing",
                purpose=f"Supplies full requirement of Phosphorus ({round(net_p2o5, 1)} kg P2O5/ha) plus {round(n_supplied_by_dap, 1)} kg starter Nitrogen/ha."
            ))

        # 2. Nitrogen satisfied by Urea (after deducting N from DAP)
        remaining_n = max(0.0, net_n - n_supplied_by_dap)
        urea_per_ha = remaining_n / 0.46
        urea_total = urea_per_ha * area_ha
        urea_per_acre = urea_per_ha / 2.47105
        products.append(FertilizerProductDose(
            product_name="Urea",
            nutrient_composition="46-0-0",
            amount_per_ha_kg=round(urea_per_ha, 1),
            amount_per_acre_kg=round(urea_per_acre, 1),
            total_field_kg=round(urea_total, 1),
            bags_50kg_needed=round(urea_total / 50.0, 1),
            application_method="Split application (basal and top-dressing)",
            timing="Split as per crop growth stages",
            purpose=f"Supplies remaining {round(remaining_n, 1)} kg pure Nitrogen/ha (accounting for {round(n_supplied_by_dap, 1)} kg N already provided by DAP)."
        ))

        # 3. Potassium satisfied by MOP
        mop_per_ha = net_k2o / 0.60
        mop_total = mop_per_ha * area_ha
        mop_per_acre = mop_per_ha / 2.47105
        products.append(FertilizerProductDose(
            product_name="MOP (Muriate of Potash)",
            nutrient_composition="0-0-60",
            amount_per_ha_kg=round(mop_per_ha, 1),
            amount_per_acre_kg=round(mop_per_acre, 1),
            total_field_kg=round(mop_total, 1),
            bags_50kg_needed=round(mop_total / 50.0, 1),
            application_method="Soil application",
            timing="Basal at sowing/planting (or split for coffee)",
            purpose=f"Supplies {round(net_k2o, 1)} kg pure K2O/ha for disease resistance, water regulation, and crop quality."
        ))

        return products

    def generate_split_schedule(
        self,
        crop: str,
        products: List[FertilizerProductDose],
        area_ha: float
    ) -> List[SplitScheduleItem]:
        """Generate growth-stage split schedule specific to the crop guidelines."""
        split_rules = self.rules[crop]["split_schedule"]
        schedule = []
        
        # Product dictionary
        prod_map = {p.product_name: p for p in products}
        dap = prod_map.get("DAP (Di-Ammonium Phosphate)")
        urea = prod_map.get("Urea")
        mop = prod_map.get("MOP (Muriate of Potash)")

        for rule in split_rules:
            stage_ferts = []
            n_pct = rule["n_percent"] / 100.0
            p_pct = rule["p_percent"] / 100.0
            k_pct = rule["k_percent"] / 100.0
            
            if dap and p_pct > 0:
                dap_kg = round(dap.total_field_kg * p_pct, 1)
                stage_ferts.append({
                    "product": "DAP",
                    "amount_field_kg": dap_kg,
                    "bags_50kg": round(dap_kg / 50.0, 1)
                })
                
            if urea and n_pct > 0:
                urea_kg = round(urea.total_field_kg * n_pct, 1)
                stage_ferts.append({
                    "product": "Urea",
                    "amount_field_kg": urea_kg,
                    "bags_50kg": round(urea_kg / 50.0, 1)
                })
                
            if mop and k_pct > 0:
                mop_kg = round(mop.total_field_kg * k_pct, 1)
                stage_ferts.append({
                    "product": "MOP",
                    "amount_field_kg": mop_kg,
                    "bags_50kg": round(mop_kg / 50.0, 1)
                })
                
            schedule.append(SplitScheduleItem(
                stage=rule["stage"],
                timing_days_or_event=rule["timing_days_or_event"],
                fertilizers=stage_ferts,
                application_instructions=rule["instructions"]
            ))

        return schedule

    async def get_recommendation(self, input_data: SoilTestInput) -> FertilizerRecommendationResponse:
        """Execute complete personalized fertilizer recommendation pipeline."""
        crop = input_data.crop.lower()
        if crop not in self.rules:
            raise ValueError(f"Crop '{crop}' is not supported. Supported: coffee, potato, maize.")
            
        crop_meta = self.rules[crop]
        
        # 1. Area conversions
        area_ha = self.convert_area_to_hectares(input_data.field_area, input_data.area_unit)
        area_acres = area_ha * 2.47105
        
        # 2. Nutrient conversions
        norm_n, norm_p, norm_k = self.normalize_soil_nutrients(
            input_data.soil_n, input_data.soil_p, input_data.soil_k, input_data.nutrient_unit
        )
        
        # 3. Soil ratings & adjustment factors
        ratings, factors = self.classify_nutrient_rating(crop, norm_n, norm_p, norm_k)
        
        # 4. Base requirement & Soil Test Crop Response (STCR) adjustment
        base_n = crop_meta["base_nutrients_kg_per_ha"]["N"] * factors["N"]
        base_p = crop_meta["base_nutrients_kg_per_ha"]["P2O5"] * factors["P"]
        base_k = crop_meta["base_nutrients_kg_per_ha"]["K2O"] * factors["K"]
        
        pure_recommended = {
            "N": round(base_n, 1),
            "P2O5": round(base_p, 1),
            "K2O": round(base_k, 1)
        }
        
        # 5. Organic manure credits
        manure_credits = self.calculate_manure_credits(input_data.fym_applied_tons_per_ha or 0.0)
        
        # 6. Net pure nutrients required
        net_n = max(0.0, pure_recommended["N"] - manure_credits["N"])
        net_p = max(0.0, pure_recommended["P2O5"] - manure_credits["P2O5"])
        net_k = max(0.0, pure_recommended["K2O"] - manure_credits["K2O"])
        
        net_nutrients = {
            "N": round(net_n, 1),
            "P2O5": round(net_p, 1),
            "K2O": round(net_k, 1)
        }
        
        # 7. Solve commercial fertilizer formulation (avoid double counting)
        products = self.solve_commercial_fertilizers(net_n, net_p, net_k, area_ha, area_acres)
        
        # 8. Generate split schedule
        schedule = self.generate_split_schedule(crop, products, area_ha)
        
        # 9. Real weather forecast integration
        weather_raw = await weather_service.get_forecast(
            latitude=input_data.latitude,
            longitude=input_data.longitude,
            location_name=input_data.location or "Karnataka, India"
        )
        weather_adj = WeatherAdjustment(
            location_checked=weather_raw["location_checked"],
            forecast_timestamp=weather_raw["forecast_timestamp"],
            rainfall_next_48h_mm=weather_raw["rainfall_next_48h_mm"],
            rain_probability_percent=weather_raw["rain_probability_percent"],
            recommendation_status=weather_raw["recommendation_status"],
            advisory_note=weather_raw["advisory_note"],
            data_source=weather_raw["data_source"]
        )
        
        # 10. Organic alternatives and soil-health guidance
        organic_alts = [
            OrganicAlternative(
                practice_or_input="Farmyard Manure (Well-rotted FYM) or Vermicompost",
                quantity=f"{round(area_ha * 5, 1)} tons total for field ({5.0} t/ha)",
                nutrient_benefit="Supplies balanced macro and micro-nutrients slowly over the growing season.",
                soil_health_impact="Improves soil organic carbon (SOC), water retention capacity, and microbial biodiversity."
            ),
            OrganicAlternative(
                practice_or_input="Biofertilizers (Azotobacter / Azospirillum + PSB)",
                quantity="5 kg/ha mixed with 100 kg compost",
                nutrient_benefit="Fixes 20-25 kg atmospheric N/ha and solubilizes native fixed soil phosphorus.",
                soil_health_impact="Enhances root mycorrhizal colonization and rhizosphere health."
            )
        ]
        
        # 11. Explanations and citations
        explanation = (
            f"Recommendations formulated for {crop_meta['crop_name']} based on {crop_meta['authority']}. "
            f"Your soil test indicates Available Nitrogen is {ratings['N']} ({round(norm_n, 1)} kg/ha), "
            f"Phosphorus is {ratings['P']} ({round(norm_p, 1)} kg/ha), and Potassium is {ratings['K']} ({round(norm_k, 1)} kg/ha). "
            f"Gross nutrient requirement adjusted for soil fertility: {pure_recommended['N']} kg N, {pure_recommended['P2O5']} kg P2O5, {pure_recommended['K2O']} kg K2O per hectare. "
        )
        if input_data.fym_applied_tons_per_ha and input_data.fym_applied_tons_per_ha > 0:
            explanation += (
                f"Accounting for {input_data.fym_applied_tons_per_ha} t/ha of organic manure applied, nutrient credits of "
                f"{manure_credits['N']} kg N, {manure_credits['P2O5']} kg P2O5, and {manure_credits['K2O']} kg K2O have been deducted from your commercial fertilizer requirements. "
            )
        explanation += (
            "DAP is used to fulfill Phosphorus requirements, and the Nitrogen naturally present in DAP (18%) has been deducted from your Urea requirement to prevent dangerous and costly double-counting."
        )
        
        safety_warnings = []
        if input_data.soil_ph is not None:
            if input_data.soil_ph < 5.5:
                safety_warnings.append(
                    f"Soil pH is strongly acidic ({input_data.soil_ph}). Phosphorus will be locked as insoluble iron/aluminum phosphates. "
                    f"Apply agricultural lime (calcium carbonate) at 1.5 - 2.0 t/ha at least 3 weeks before planting."
                )
            elif input_data.soil_ph > 8.0:
                safety_warnings.append(
                    f"Soil pH is alkaline ({input_data.soil_ph}). Ammonia volatilization from Urea will be high. "
                    "Incorporate Urea immediately 5-8 cm into the soil or apply with irrigation."
                )
        
        missing_input_notes = []
        if input_data.soil_ph is None:
            missing_input_notes.append("Soil pH was not provided; assumed neutral (6.5). If your soil is acidic, liming will be required.")
        if input_data.organic_carbon_percent is None:
            missing_input_notes.append("Organic Carbon % not provided; testing is recommended to calibrate long-term organic matter targets.")

        return FertilizerRecommendationResponse(
            crop=crop,
            growth_stage=input_data.growth_stage,
            area_summary={
                "input_area": input_data.field_area,
                "input_unit": input_data.area_unit,
                "area_in_hectares": round(area_ha, 3),
                "area_in_acres": round(area_acres, 3)
            },
            soil_test_rating=ratings,
            pure_nutrients_recommended_kg_per_ha=pure_recommended,
            manure_credits_deducted_kg_per_ha=manure_credits,
            net_pure_nutrients_needed_kg_per_ha=net_nutrients,
            commercial_fertilizers=products,
            split_schedule=schedule,
            weather_adjustment=weather_adj,
            organic_alternatives=organic_alts,
            explanation=explanation,
            citations=crop_meta["citations"],
            safety_warnings=safety_warnings,
            missing_input_notes=missing_input_notes
        )

fertilizer_service = FertilizerService()
