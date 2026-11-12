from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any

class SoilTestInput(BaseModel):
    crop: str = Field(..., description="Target crop: coffee, potato, or maize")
    growth_stage: str = Field(..., description="e.g. vegetative, flowering, tuber_initiation, knee_high, bearing")
    location: Optional[str] = Field("Karnataka, India", description="Farmer district/state/region")
    latitude: Optional[float] = Field(None, description="Optional GPS latitude for weather check")
    longitude: Optional[float] = Field(None, description="Optional GPS longitude for weather check")
    
    # Area
    field_area: float = Field(..., gt=0, description="Numerical field area size")
    area_unit: str = Field(..., description="acres, hectares, guntas, bighas, cents")
    
    # Soil nutrient values
    soil_n: float = Field(..., ge=0, description="Available Soil Nitrogen")
    soil_p: float = Field(..., ge=0, description="Available Soil Phosphorus")
    soil_k: float = Field(..., ge=0, description="Available Soil Potassium")
    nutrient_unit: str = Field("kg/ha", description="kg/ha, ppm, lb/acre")
    
    # Soil properties
    soil_ph: Optional[float] = Field(None, ge=3.0, le=11.0, description="Soil pH (3.0 - 11.0)")
    organic_carbon_percent: Optional[float] = Field(None, ge=0.0, le=10.0, description="Soil Organic Carbon %")
    moisture_status: Optional[str] = Field("adequate", description="dry, adequate, wet, waterlogged")
    irrigation_context: Optional[str] = Field("rainfed", description="rainfed, drip, sprinkler, furrow")
    
    # Previous applications
    fym_applied_tons_per_ha: Optional[float] = Field(0.0, ge=0.0, description="Farmyard manure / compost applied in tons/ha")
    recent_fertilizers: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Recent fertilizer doses applied")
    
    # Confirmation flag: farmers MUST confirm extracted OCR values before calculations
    user_confirmed: bool = Field(True, description="True if farmer confirmed values")

    @field_validator("crop")
    @classmethod
    def validate_crop(cls, v: str) -> str:
        valid_crops = {"coffee", "potato", "maize"}
        clean = v.strip().lower()
        if clean not in valid_crops:
            raise ValueError(f"Crop '{v}' not supported. Supported crops are: {', '.join(sorted(valid_crops))}")
        return clean

    @field_validator("area_unit")
    @classmethod
    def validate_area_unit(cls, v: str) -> str:
        valid_units = {"acres", "acre", "hectares", "hectare", "ha", "guntas", "guntha", "bighas", "bigha", "cents", "cent"}
        clean = v.strip().lower()
        if clean not in valid_units:
            raise ValueError(f"Area unit '{v}' not supported. Use acres, hectares, guntas, bighas, or cents.")
        return clean


class FertilizerProductDose(BaseModel):
    product_name: str
    nutrient_composition: str # e.g. "46-0-0"
    amount_per_ha_kg: float
    amount_per_acre_kg: float
    total_field_kg: float
    bags_50kg_needed: float
    application_method: str # basal, top_dressing, fertigation
    timing: str # e.g. "At sowing/planting"
    purpose: str


class SplitScheduleItem(BaseModel):
    stage: str
    timing_days_or_event: str
    fertilizers: List[Dict[str, Any]]
    application_instructions: str


class WeatherAdjustment(BaseModel):
    location_checked: str
    forecast_timestamp: str
    rainfall_next_48h_mm: float
    rain_probability_percent: int
    recommendation_status: str # "proceed", "hold_nitrogen", "delay_application"
    advisory_note: str
    data_source: str # "Open-Meteo Live API" or "Cached/Fallback"


class OrganicAlternative(BaseModel):
    practice_or_input: str
    quantity: str
    nutrient_benefit: str
    soil_health_impact: str


class FertilizerRecommendationResponse(BaseModel):
    id: Optional[int] = None
    crop: str
    growth_stage: str
    area_summary: Dict[str, Any]
    soil_test_rating: Dict[str, str] # e.g. {"N": "Low", "P": "Medium", "K": "High"}
    
    # Pure nutrients
    pure_nutrients_recommended_kg_per_ha: Dict[str, float] # pure N, P2O5, K2O
    manure_credits_deducted_kg_per_ha: Dict[str, float]
    net_pure_nutrients_needed_kg_per_ha: Dict[str, float]
    
    # Commercial Products
    commercial_fertilizers: List[FertilizerProductDose]
    split_schedule: List[SplitScheduleItem]
    
    # Guidance & Explanations
    weather_adjustment: WeatherAdjustment
    organic_alternatives: List[OrganicAlternative]
    explanation: str
    citations: List[Dict[str, str]]
    safety_warnings: List[str]
    missing_input_notes: List[str]
