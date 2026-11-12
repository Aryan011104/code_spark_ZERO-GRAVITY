from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class DiseaseAssessmentRequest(BaseModel):
    crop: str = Field(..., description="Target crop (coffee, potato, maize, etc.)")
    plant_part: str = Field(..., description="leaf, stem, fruit, root, tuber, whole_plant")
    symptoms: List[str] = Field(..., min_length=1, description="Observed visual symptoms e.g. yellow_spots, brown_margins, wilting")
    symptom_duration_days: Optional[int] = Field(None, ge=1, le=180, description="Duration since first noticed (days)")
    growth_stage: Optional[str] = Field(None, description="vegetative, flowering, fruiting, harvesting")
    location: Optional[str] = Field("Karnataka, India", description="Farmer location/region")
    image_base64: Optional[str] = Field(None, description="Base64 encoded photograph string")


class ImageQualityResult(BaseModel):
    is_acceptable: bool
    sharpness_score: float # Laplacian variance score
    is_blurry: bool
    brightness_score: float # Average pixel luminance
    is_underexposed: bool
    is_overexposed: bool
    is_plant_detected: bool
    message: str
    rejection_reason: Optional[str] = None


class AlternativeCause(BaseModel):
    condition_name: str
    condition_type: str # disease, pest, nutrient_deficiency, environmental_stress
    likelihood_score: float
    distinguishing_features: str


class IPMMeasure(BaseModel):
    tier: str # Cultural / Sanitation, Biological / Organic, Chemical (strictly verified)
    action: str
    timing: str
    safety_precaution: str


class ExpertReferral(BaseModel):
    is_recommended: bool
    urgency: str # routine, moderate, high
    reason: str
    recommended_contact: str
    samples_to_preserve: str


class DiseaseAssessmentResponse(BaseModel):
    case_reference: str
    crop: str
    plant_part: str
    image_quality: ImageQualityResult
    
    # Diagnosis
    primary_condition: str
    scientific_name: Optional[str] = None
    condition_type: str # fungal_disease, bacterial_disease, pest_damage, nutrient_deficiency, environmental_stress, healthy
    calibrated_confidence: float # Calibrated probability between 0.0 and 1.0
    confidence_level: str # High, Moderate, Low, Inconclusive
    is_inconclusive: bool
    
    # Explanations
    supporting_observations: List[str]
    alternative_causes: List[AlternativeCause]
    ipm_recommendations: List[IPMMeasure]
    follow_up_questions: List[str]
    expert_referral: ExpertReferral
    unsupported_crop_note: Optional[str] = None
    citations: List[Dict[str, str]]
