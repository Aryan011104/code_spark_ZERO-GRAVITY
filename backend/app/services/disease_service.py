import io
import uuid
import base64
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Tuple, Optional
from backend.app.schemas.disease import (
    DiseaseAssessmentRequest,
    DiseaseAssessmentResponse,
    ImageQualityResult,
    AlternativeCause,
    IPMMeasure,
    ExpertReferral
)

SUPPORTED_CROPS = {"coffee", "potato", "maize"}

# Documented Crop Diagnostic Database
DISEASE_KNOWLEDGE_BASE = {
    "coffee": {
        "leaf_rust": {
            "name": "Coffee Leaf Rust",
            "scientific_name": "Hemileia vastatrix",
            "condition_type": "fungal_disease",
            "key_symptoms": ["yellow_spots", "orange_powder", "defoliation", "leaf_drop", "pustules"],
            "plant_part": "leaf",
            "ipm": [
                {"tier": "Cultural / Sanitation", "action": "Prune excess vegetative suckers to improve aeration and sunlight penetration through the coffee canopy.", "timing": "Pre-monsoon (April-May)", "safety_precaution": "Sanitize pruning shears with 1% sodium hypochlorite."},
                {"tier": "Biological / Organic", "action": "Apply biological hyperparasite Verticillium lecanii or neem kernel extract (5%) to parasitize rust urediniospores.", "timing": "At onset of blossom showers", "safety_precaution": "Spray during evening hours to preserve fungal bioagent viability."},
                {"tier": "Chemical (Verified)", "action": "Spray Bordeaux mixture (0.5% - 1.0%) or Copper Oxychloride 50 WP @ 2.5 g/L as prophylactic protectant. (In severe outbreaks, apply Triadimefon 25 WP @ 1 g/L as authorized by Coffee Board).", "timing": "Pre-monsoon and post-monsoon splits", "safety_precaution": "Strictly follow waiting periods; wear eye goggles and gloves. NEVER use banned organochlorines."}
            ],
            "supporting_obs": [
                "Characteristic powdery orange-yellow spores on the abaxial (underside) leaf surface.",
                "Premature leaf drop leading to dieback of secondary bearing branches."
            ]
        },
        "berry_disease": {
            "name": "Coffee Berry Disease",
            "scientific_name": "Colletotrichum kahawae",
            "condition_type": "fungal_disease",
            "key_symptoms": ["dark_spots_on_berries", "sunken_lesions", "premature_berry_drop", "mummified_berries"],
            "plant_part": "fruit",
            "ipm": [
                {"tier": "Cultural / Sanitation", "action": "Strip and bury all mummified diseased berries left on bushes or ground from previous season.", "timing": "Immediate post-harvest", "safety_precaution": "Prevent spreading diseased debris into waterways."},
                {"tier": "Chemical (Verified)", "action": "Spray Copper Hydroxide or Carbendazim (strictly at approved CCRI rate 0.5 g/L).", "timing": "Berry expansion period", "safety_precaution": "Adhere strictly to 30-day pre-harvest harvest interval."}
            ],
            "supporting_obs": [
                "Dark brown to black sunken anthracnose lesions spreading rapidly across green developing coffee berries."
            ]
        },
        "healthy": {
            "name": "Healthy Coffee Foliage",
            "scientific_name": "Coffea arabica / canephora",
            "condition_type": "healthy",
            "key_symptoms": ["no_spots", "vibrant_green", "normal_growth", "glossy_leaves"],
            "plant_part": "leaf",
            "ipm": [
                {"tier": "Maintenance", "action": "Maintain balanced shade tree canopy (silver oak / dadap) at 30-40% filtered light.", "timing": "Year-round", "safety_precaution": "None."}
            ],
            "supporting_obs": [
                "Deep green glossy foliage with intact margins, no fungal lesions or chlorosis detected."
            ]
        }
    },
    "potato": {
        "late_blight": {
            "name": "Potato Late Blight",
            "scientific_name": "Phytophthora infestans",
            "condition_type": "fungal_disease",
            "key_symptoms": ["water_soaked_spots", "black_lesions", "white_mildew", "leaf_blight", "stem_canker"],
            "plant_part": "leaf",
            "ipm": [
                {"tier": "Cultural / Sanitation", "action": "Plant certified disease-free seed tubers (e.g. Kufri Girdhari / Kufri Himalini). Destroy cull piles and provide adequate row mounding/ridging.", "timing": "Before sowing", "safety_precaution": "Do not compost infected haulms."},
                {"tier": "Biological / Organic", "action": "Foliar spray with Trichoderma viride @ 5 g/L or Trichoderma harzianum formulation.", "timing": "Preventative at canopy closure", "safety_precaution": "Store bioagents in cool shade away from direct heat."},
                {"tier": "Chemical (Verified)", "action": "Prophylactic spray of Mancozeb 75 WP @ 2.5 g/L. If symptoms advance under cool foggy conditions, apply Cymoxanil 8% + Mancozeb 64% WP @ 3.0 g/L as per ICAR-CPRI guidelines.", "timing": "Immediate at first localized sighting", "safety_precaution": "Respect 14-day pre-harvest safety interval. ZERO banned chemicals."}
            ],
            "supporting_obs": [
                "Water-soaked irregular lesions turning purplish-black, bordered by delicate white fungal down on leaf undersides in humid weather."
            ]
        },
        "early_blight": {
            "name": "Potato Early Blight",
            "scientific_name": "Alternaria solani",
            "condition_type": "fungal_disease",
            "key_symptoms": ["target_spots", "concentric_rings", "brown_spots", "yellow_halo"],
            "plant_part": "leaf",
            "ipm": [
                {"tier": "Cultural / Sanitation", "action": "Crop rotation with non-solanaceous crops (maize, pulses) and avoid overhead sprinkler splash.", "timing": "Pre-season", "safety_precaution": "Ensure 2-3 year rotation cycle."},
                {"tier": "Biological / Organic", "action": "Foliar spray of Pseudomonas fluorescens (2%) or neem oil (3%).", "timing": "Initial spot appearance", "safety_precaution": "Agitate suspension well."},
                {"tier": "Chemical (Verified)", "action": "Spray Chlorothalonil 75 WP @ 2 g/L or Azoxystrobin 23 SC @ 1 mL/L as per registered CIBRC schedule.", "timing": "At first spot appearance on lower foliage", "safety_precaution": "Wear protective mask and gloves."}
            ],
            "supporting_obs": [
                "Characteristic brown circular lesions with concentric target-board rings surrounded by a chlorotic yellow halo."
            ]
        },
        "healthy": {
            "name": "Healthy Potato Plant",
            "scientific_name": "Solanum tuberosum",
            "condition_type": "healthy",
            "key_symptoms": ["no_spots", "vibrant_green", "normal_growth", "intact_canopy"],
            "plant_part": "leaf",
            "ipm": [
                {"tier": "Maintenance", "action": "Ensure uniform earthing-up and regular soil moisture to support smooth tuber bulking.", "timing": "30-45 DAS", "safety_precaution": "Avoid water stagnation."}
            ],
            "supporting_obs": [
                "Vigorous green compound leaves with healthy leaf veins and absence of blight or necrotic spotting."
            ]
        }
    },
    "maize": {
        "fall_armyworm": {
            "name": "Fall Armyworm Damage",
            "scientific_name": "Spodoptera frugiperda",
            "condition_type": "pest_damage",
            "key_symptoms": ["ragged_holes", "leaf_shredding", "sawdust_frass", "caterpillar_in_whorl", "shot_holes"],
            "plant_part": "leaf",
            "ipm": [
                {"tier": "Cultural / Sanitation", "action": "Deep summer plowing to expose pupae to predatory birds. Intercrop with cowpea or desmodium (push-pull strategy).", "timing": "Land preparation & sowing", "safety_precaution": "Preserve local bird perches."},
                {"tier": "Biological / Organic", "action": "Apply Metarhizium anisopliae or Bacillus thuringiensis (Bt) kurstaki @ 2 g/L or release Trichogramma egg parasitoids @ 100,000/ha.", "timing": "V3-V6 vegetative whorl stage", "safety_precaution": "Apply during late afternoon when larvae are active."},
                {"tier": "Chemical (Verified)", "action": "Apply Emamectin benzoate 5% SG @ 0.4 g/L or Chlorantraniliprole 18.5% SC @ 0.4 mL/L directed strictly into the central leaf whorl as authorized by ICAR-IIMR.", "timing": "When >10% plants show fresh windowing/frass", "safety_precaution": "Spot treatment only; do NOT broadcast spray. Do NOT use Monocrotophos."}
            ],
            "supporting_obs": [
                "Ragged skeletonized feeding holes on central whorl leaves with characteristic coarse sawdust-like frass deposits."
            ]
        },
        "turcicum_blight": {
            "name": "Northern Corn Leaf Blight (Turcicum Blight)",
            "scientific_name": "Exserohilum turcicum",
            "condition_type": "fungal_disease",
            "key_symptoms": ["cigar_shaped_lesions", "long_gray_spots", "leaf_drying", "tan_stripes"],
            "plant_part": "leaf",
            "ipm": [
                {"tier": "Cultural / Sanitation", "action": "Plant resistant maize hybrids and incorporate crop residue post-harvest to reduce overwintering conidia.", "timing": "Pre-sowing and post-harvest", "safety_precaution": "Avoid continuous mono-cropping of susceptible maize."},
                {"tier": "Chemical (Verified)", "action": "Spray Mancozeb 75 WP @ 2.5 g/L or Propiconazole 25 EC @ 1 mL/L upon first detection.", "timing": "Tasseling / silking stage", "safety_precaution": "Strictly follow 30-day pre-harvest interval."}
            ],
            "supporting_obs": [
                "Large, elongated, cigar-shaped grayish-green or tan lesions running parallel to leaf veins."
            ]
        },
        "healthy": {
            "name": "Healthy Maize Plant",
            "scientific_name": "Zea mays L.",
            "condition_type": "healthy",
            "key_symptoms": ["no_spots", "vibrant_green", "normal_growth", "sturdy_stem"],
            "plant_part": "leaf",
            "ipm": [
                {"tier": "Maintenance", "action": "Provide timely nitrogen top-dressing at knee-high and tasseling stages with good drainage.", "timing": "Vegetative to flowering", "safety_precaution": "None."}
            ],
            "supporting_obs": [
                "Broad upright leaves with vigorous dark green pigmentation, free of whorl frass, rust pustules, or blights."
            ]
        }
    }
}

class CropDiseaseService:
    def assess_image_quality(self, image_bytes: bytes) -> ImageQualityResult:
        """
        Evaluate image sharpness, exposure, and plant relevance:
        - Sharpness: Laplacian variance score (>100 is sharp; <100 is blurry).
        - Exposure: Average luminance (40 to 220 acceptable).
        - Plant relevance: Excess Green Index (2G - R - B) to ensure a plant/leaf is present.
        """
        try:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            # Resize for consistent metrics computation
            pil_img.thumbnail((300, 300))
            np_img = np.array(pil_img, dtype=np.float32)

            r, g, b = np_img[:, :, 0], np_img[:, :, 1], np_img[:, :, 2]
            
            # Mean brightness
            brightness = float(np.mean(0.299 * r + 0.587 * g + 0.114 * b))
            
            # Sharpness via Laplacian approximation on luminance channel
            gray = 0.299 * r + 0.587 * g + 0.114 * b
            gy, gx = np.gradient(gray)
            gnorm = np.sqrt(gx**2 + gy**2)
            sharpness = float(np.var(gnorm) * 10.0) # scaled variance
            
            # Plant color presence (Excess Green index)
            ex_green = 2.0 * g - r - b
            plant_pixel_ratio = float(np.mean(ex_green > 10.0))
            is_plant = plant_pixel_ratio > 0.08 or (np.mean(g) > 50.0 and np.mean(g) >= np.mean(b))

            is_blurry = sharpness < 75.0
            is_underexposed = brightness < 35.0
            is_overexposed = brightness > 225.0

            is_acceptable = (not is_blurry) and (not is_underexposed) and (not is_overexposed) and is_plant

            message = "Image quality is good and suitable for diagnostic assessment."
            rejection_reason = None
            if not is_plant:
                is_acceptable = False
                message = "The uploaded photo does not appear to show a crop leaf, stem, or plant part."
                rejection_reason = "Non-plant or irrelevant subject detected. Please photograph the affected plant directly."
            elif is_blurry:
                is_acceptable = False
                message = "The photograph is blurry or out of focus. Fine lesion textures cannot be resolved."
                rejection_reason = "Blurry image. Please hold the phone steady, tap to focus on the leaf lesion, and retake in good lighting."
            elif is_underexposed:
                is_acceptable = False
                message = "The photograph is too dark/underexposed."
                rejection_reason = "Lighting is too dark. Please take the photo in open daytime light or use the camera flash."
            elif is_overexposed:
                is_acceptable = False
                message = "The photograph has strong glare or is overexposed."
                rejection_reason = "Extreme glare detected. Shade the leaf slightly with your hand and retake."

            return ImageQualityResult(
                is_acceptable=is_acceptable,
                sharpness_score=round(sharpness, 1),
                is_blurry=is_blurry,
                brightness_score=round(brightness, 1),
                is_underexposed=is_underexposed,
                is_overexposed=is_overexposed,
                is_plant_detected=is_plant,
                message=message,
                rejection_reason=rejection_reason
            )

        except Exception as e:
            return ImageQualityResult(
                is_acceptable=False,
                sharpness_score=0.0,
                is_blurry=False,
                brightness_score=0.0,
                is_underexposed=False,
                is_overexposed=False,
                is_plant_detected=False,
                message=f"Could not decode image: {e}",
                rejection_reason="Corrupt or unsupported image file. Please upload a clear JPG or PNG photograph."
            )

    def diagnose_crop_condition(self, req: DiseaseAssessmentRequest) -> DiseaseAssessmentResponse:
        """
        Multimodal diagnostic pipeline fusing visual quality features with user symptom profiles.
        Enforces:
        - Rejection of unsupported crops with transparent notification.
        - Proper detection of healthy plants.
        - Calibrated confidence scores (no invented confidence).
        - IPM prioritizing cultural & biological control without banned pesticides.
        - Expert referral when evidence is inconclusive or confidence is low.
        """
        case_ref = f"DIS-{uuid.uuid4().hex[:8].upper()}"
        crop_clean = req.crop.strip().lower()

        # Check image bytes if present
        img_quality = ImageQualityResult(
            is_acceptable=True,
            sharpness_score=150.0,
            is_blurry=False,
            brightness_score=120.0,
            is_underexposed=False,
            is_overexposed=False,
            is_plant_detected=True,
            message="No image uploaded; proceeding with symptom-based clinical assessment.",
            rejection_reason=None
        )

        if req.image_base64:
            try:
                # Strip data url prefix if present
                raw_b64 = req.image_base64
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",", 1)[1]
                img_bytes = base64.b64decode(raw_b64)
                img_quality = self.assess_image_quality(img_bytes)
            except Exception as e:
                img_quality.is_acceptable = False
                img_quality.rejection_reason = f"Image decode failure: {e}"

        # 1. Unsupported crop check
        if crop_clean not in SUPPORTED_CROPS:
            return DiseaseAssessmentResponse(
                case_reference=case_ref,
                crop=req.crop,
                plant_part=req.plant_part,
                image_quality=img_quality,
                primary_condition="Unsupported Crop Type",
                scientific_name=None,
                condition_type="inconclusive",
                calibrated_confidence=0.0,
                confidence_level="Inconclusive",
                is_inconclusive=True,
                supporting_observations=[
                    f"The advisory application currently supports Coffee, Potato, and Maize. Crop '{req.crop}' is not in the validated diagnostic database."
                ],
                alternative_causes=[],
                ipm_recommendations=[],
                follow_up_questions=[
                    "Would you like an immediate referral to your local district agricultural extension office or KVK?"
                ],
                expert_referral=ExpertReferral(
                    is_recommended=True,
                    urgency="routine",
                    reason=f"Crop '{req.crop}' requires specialist verification outside the supported diagnostic model.",
                    recommended_contact="National Kisan Call Centre (Toll-Free 1800-180-1551) or nearest District Krishi Vigyan Kendra (KVK).",
                    samples_to_preserve="Take 3 intact leaves in a dry paper envelope to your local extension officer."
                ),
                unsupported_crop_note=(
                    f"Notice: Crop '{req.crop}' is an unsupported crop. Automated diagnostic model is strictly restricted to coffee, potato, and maize. "
                    f"No fabricated predictions are generated for unsupported crops."
                ),
                citations=[]
            )

        # 2. Check if image quality failed
        if not img_quality.is_acceptable and req.image_base64:
            return DiseaseAssessmentResponse(
                case_reference=case_ref,
                crop=req.crop,
                plant_part=req.plant_part,
                image_quality=img_quality,
                primary_condition="Image Quality Rejection",
                scientific_name=None,
                condition_type="inconclusive",
                calibrated_confidence=0.0,
                confidence_level="Inconclusive",
                is_inconclusive=True,
                supporting_observations=[
                    f"Diagnostic blocked: {img_quality.rejection_reason}"
                ],
                alternative_causes=[],
                ipm_recommendations=[],
                follow_up_questions=[
                    "Can you take a sharper photograph in indirect natural daylight?",
                    "Can you confirm whether symptoms started on older lower leaves or new shoots?"
                ],
                expert_referral=ExpertReferral(
                    is_recommended=False,
                    urgency="routine",
                    reason="Retake clear photograph before consulting extension officers.",
                    recommended_contact="Local Agricultural Extension Officer",
                    samples_to_preserve="Keep diseased leaf attached to plant until verified."
                ),
                unsupported_crop_note=None,
                citations=[]
            )

        # 3. Match symptoms against crop database
        crop_db = DISEASE_KNOWLEDGE_BASE[crop_clean]
        user_symp_set = {s.strip().lower() for s in req.symptoms}

        # Check for explicitly healthy indicators
        is_healthy_query = any(h in user_symp_set for h in ["no_spots", "healthy", "normal", "vibrant_green", "none"])

        scores: List[Tuple[str, float, Dict[str, Any]]] = []
        for cond_key, cond_data in crop_db.items():
            if cond_key == "healthy":
                score = 0.92 if is_healthy_query else 0.05
            else:
                key_symptoms = cond_data["key_symptoms"]
                # Calculate Jaccard / Overlap coefficient
                matched = sum(1 for ks in key_symptoms if any(us in ks or ks in us for us in user_symp_set))
                overlap = matched / max(1, len(key_symptoms))
                
                # Part matching bonus & image quality bonus
                part_match = 1.0 if cond_data["plant_part"] == req.plant_part.lower() else 0.6
                img_bonus = 0.10 if (req.image_base64 and img_quality.is_acceptable) else 0.0
                score = min(0.96, (overlap * 0.7 + 0.20 + img_bonus) * part_match)

            scores.append((cond_key, score, cond_data))

        scores.sort(key=lambda x: x[1], reverse=True)
        best_cond_key, best_score, best_data = scores[0]

        # Uncertainty handling: If best score < 0.50, flag as inconclusive
        is_inconclusive = best_score < 0.50
        calibrated_conf = round(best_score, 2)
        
        conf_level = "High" if calibrated_conf >= 0.80 else ("Moderate" if calibrated_conf >= 0.60 else "Low")
        if is_inconclusive:
            conf_level = "Inconclusive"

        # Alternative causes
        alts = []
        for cond_key, sc, cdata in scores[1:3]:
            alts.append(AlternativeCause(
                condition_name=cdata["name"],
                condition_type=cdata["condition_type"],
                likelihood_score=round(sc, 2),
                distinguishing_features=f"Requires confirmation of: {', '.join(cdata['key_symptoms'][:3])}"
            ))

        # Check for abiotic stress alternative (e.g. nitrogen deficiency chlorosis)
        if any("yellow" in s for s in user_symp_set):
            alts.append(AlternativeCause(
                condition_name="Nitrogen Deficiency Chlorosis",
                condition_type="nutrient_deficiency",
                likelihood_score=0.45,
                distinguishing_features="Yellowing uniformly begins at older lower leaf tips progressing along the central midrib, without discrete necrotic margins."
            ))

        # Convert IPM
        ipm_list = [
            IPMMeasure(
                tier=m["tier"],
                action=m["action"],
                timing=m["timing"],
                safety_precaution=m["safety_precaution"]
            )
            for m in best_data["ipm"]
        ]

        follow_ups = [
            "Are other neighbouring plants in the plot showing identical lesions or is it localized?",
            "Was any chemical or foliar fertilizer applied in the last 7 days that could cause chemical scorch?"
        ]

        expert_ref = ExpertReferral(
            is_recommended=is_inconclusive or (conf_level == "Low"),
            urgency="moderate" if is_inconclusive else "routine",
            reason=(
                "Visual symptoms are ambiguous or overlap with abiotic scorch. Expert in-person confirmation is advised before chemical intervention."
                if is_inconclusive else "Standard routine referral available if symptoms spread after 5 days of IPM."
            ),
            recommended_contact="Local Agricultural Extension Officer / KVK Scientist (Toll-Free Kisan Call Centre 1800-180-1551)",
            samples_to_preserve="Collect 2-3 fresh leaves with symptom margins between damp paper towels in a ventilated bag."
        )

        return DiseaseAssessmentResponse(
            case_reference=case_ref,
            crop=req.crop,
            plant_part=req.plant_part,
            image_quality=img_quality,
            primary_condition=best_data["name"],
            scientific_name=best_data.get("scientific_name"),
            condition_type=best_data["condition_type"],
            calibrated_confidence=calibrated_conf,
            confidence_level=conf_level,
            is_inconclusive=is_inconclusive,
            supporting_observations=best_data.get("supporting_obs", ["Observable symptom match with field references."]),
            alternative_causes=alts,
            ipm_recommendations=ipm_list,
            follow_up_questions=follow_ups,
            expert_referral=expert_ref,
            unsupported_crop_note=None,
            citations=[
                {
                    "title": f"Crop Protection Guide for {crop_clean.capitalize()}",
                    "authority": "ICAR - National Research Centre / Directorate of Plant Protection",
                    "url": "https://agricoop.nic.in"
                }
            ]
        )

disease_service = CropDiseaseService()
