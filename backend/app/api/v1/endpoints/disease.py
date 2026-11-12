from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import base64
import json
from backend.app.schemas.disease import DiseaseAssessmentRequest, DiseaseAssessmentResponse
from backend.app.services.disease_service import disease_service
from backend.app.db.session import get_db
from backend.app.db.models import DiseaseCase

router = APIRouter()

@router.post("/diagnose", response_model=DiseaseAssessmentResponse)
async def diagnose_crop_disease(
    payload: DiseaseAssessmentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform multimodal crop disease assessment from visual features and user symptoms.
    Provides calibrated confidence, non-chemical/chemical IPM measures, and expert referral.
    """
    try:
        diag = disease_service.diagnose_crop_condition(payload)
        
        # Persist case to database
        db_case = DiseaseCase(
            case_reference=diag.case_reference,
            crop=diag.crop,
            plant_part=diag.plant_part,
            symptoms=payload.symptoms,
            symptom_duration_days=payload.symptom_duration_days,
            growth_stage=payload.growth_stage,
            location=payload.location,
            image_quality_passed=diag.image_quality.is_acceptable,
            quality_notes=diag.image_quality.message,
            primary_condition=diag.primary_condition,
            condition_type=diag.condition_type,
            calibrated_confidence=diag.calibrated_confidence,
            is_inconclusive=diag.is_inconclusive,
            alternative_causes=[a.model_dump() for a in diag.alternative_causes],
            supporting_observations=diag.supporting_observations,
            ipm_measures=[m.model_dump() for m in diag.ipm_recommendations],
            follow_up_questions=diag.follow_up_questions,
            expert_referral=diag.expert_referral.model_dump() if diag.expert_referral else None
        )
        db.add(db_case)
        await db.commit()
        return diag
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic service error: {str(e)}")


@router.post("/diagnose-form")
async def diagnose_crop_disease_form(
    crop: str = Form(...),
    plant_part: str = Form(...),
    symptoms: str = Form(...), # JSON string of symptoms list
    symptom_duration_days: int = Form(3),
    growth_stage: str = Form("vegetative"),
    location: str = Form("Karnataka, India"),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Multipart form-data endpoint supporting direct camera photograph uploads."""
    image_b64 = None
    if file:
        file_bytes = await file.read()
        if file_bytes:
            image_b64 = base64.b64encode(file_bytes).decode("utf-8")
            
    try:
        symp_list = json.loads(symptoms) if symptoms.startswith("[") else [s.strip() for s in symptoms.split(",")]
    except Exception:
        symp_list = [symptoms]

    req = DiseaseAssessmentRequest(
        crop=crop,
        plant_part=plant_part,
        symptoms=symp_list,
        symptom_duration_days=symptom_duration_days,
        growth_stage=growth_stage,
        location=location,
        image_base64=image_b64
    )
    return await diagnose_crop_disease(req, db)
