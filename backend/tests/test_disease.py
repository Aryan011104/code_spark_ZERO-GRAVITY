import io
import base64
import numpy as np
from PIL import Image
from backend.app.schemas.disease import DiseaseAssessmentRequest
from backend.app.services.disease_service import disease_service

def create_synthetic_image(sharpness: str = "sharp", color: str = "green") -> str:
    """Helper to generate synthetic test images encoded as base64."""
    if sharpness == "sharp":
        # Create a textured image with high edge variance
        arr = np.random.randint(50, 200, (150, 150, 3), dtype=np.uint8)
        if color == "green":
            arr[:, :, 1] = np.clip(arr[:, :, 1] + 60, 0, 255) # Rich green
    elif sharpness == "blurry":
        # Flat image with minimal edge variance (Laplacian var < 10)
        arr = np.full((150, 150, 3), 100, dtype=np.uint8)
    elif sharpness == "dark":
        # Underexposed image (mean luminance < 20)
        arr = np.full((150, 150, 3), 15, dtype=np.uint8)
    else:
        arr = np.random.randint(0, 255, (150, 150, 3), dtype=np.uint8)

    img = Image.fromarray(arr)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def test_supported_disease_potato_late_blight():
    """Verify accurate diagnosis of Potato Late Blight with symptoms and IPM measures."""
    sharp_img = create_synthetic_image("sharp", "green")
    req = DiseaseAssessmentRequest(
        crop="potato",
        plant_part="leaf",
        symptoms=["water_soaked_spots", "black_lesions", "leaf_blight"],
        symptom_duration_days=4,
        image_base64=sharp_img
    )
    res = disease_service.diagnose_crop_condition(req)
    
    assert res.crop == "potato"
    assert res.primary_condition == "Potato Late Blight"
    assert res.scientific_name == "Phytophthora infestans"
    assert res.calibrated_confidence >= 0.70
    assert not res.is_inconclusive
    assert len(res.ipm_recommendations) >= 3
    # Ensure no banned chemicals are recommended
    all_ipm_text = " ".join([m.action for m in res.ipm_recommendations]).lower()
    assert "endosulfan" not in all_ipm_text
    assert "monocrotophos" not in all_ipm_text
    assert "paraquat" not in all_ipm_text


def test_healthy_plant_assessment():
    """Verify that plants showing no symptoms are diagnosed as Healthy."""
    req = DiseaseAssessmentRequest(
        crop="maize",
        plant_part="leaf",
        symptoms=["no_spots", "healthy", "vibrant_green"],
        growth_stage="knee_high"
    )
    res = disease_service.diagnose_crop_condition(req)
    
    assert res.primary_condition == "Healthy Maize Plant"
    assert res.condition_type == "healthy"
    assert res.calibrated_confidence >= 0.85


def test_low_quality_blurry_image_rejection():
    """Verify that blurry images are flagged with a polite request for a clearer photo."""
    blurry_img = create_synthetic_image("blurry")
    req = DiseaseAssessmentRequest(
        crop="coffee",
        plant_part="leaf",
        symptoms=["yellow_spots"],
        image_base64=blurry_img
    )
    res = disease_service.diagnose_crop_condition(req)
    
    assert not res.image_quality.is_acceptable
    assert res.is_inconclusive
    assert "rejection" in res.primary_condition.lower() or res.image_quality.is_blurry
    assert res.image_quality.rejection_reason is not None


def test_unsupported_crop_handling():
    """Verify that unsupported crops (e.g. Apple) are rejected without hallucinating diseases."""
    req = DiseaseAssessmentRequest(
        crop="apple",
        plant_part="leaf",
        symptoms=["scab_spots"]
    )
    res = disease_service.diagnose_crop_condition(req)
    
    assert res.is_inconclusive
    assert res.primary_condition == "Unsupported Crop Type"
    assert res.expert_referral.is_recommended
    assert "unsupported crop" in res.unsupported_crop_note.lower()
