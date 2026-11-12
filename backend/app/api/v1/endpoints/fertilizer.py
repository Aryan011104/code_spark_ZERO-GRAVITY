from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.schemas.fertilizer import SoilTestInput, FertilizerRecommendationResponse
from backend.app.services.fertilizer_service import fertilizer_service
from backend.app.services.fertilizer_ml import fertilizer_ml
from backend.app.services.ocr_service import ocr_service
from backend.app.db.session import get_db
from backend.app.db.models import FertilizerRecommendation

router = APIRouter()

@router.post("/calculate", response_model=FertilizerRecommendationResponse)
async def calculate_fertilizer_recommendation(
    payload: SoilTestInput,
    db: AsyncSession = Depends(get_db)
):
    """Calculate personalized, safety-bounded fertilizer requirements for coffee, potato, or maize."""
    try:
        rec = await fertilizer_service.get_recommendation(payload)
        
        # Persist recommendation to database
        db_rec = FertilizerRecommendation(
            crop=rec.crop,
            growth_stage=rec.growth_stage,
            location=payload.location,
            field_area=payload.field_area,
            area_unit=payload.area_unit,
            area_in_hectares=rec.area_summary["area_in_hectares"],
            soil_n=payload.soil_n,
            soil_p=payload.soil_p,
            soil_k=payload.soil_k,
            nutrient_unit=payload.nutrient_unit,
            soil_ph=payload.soil_ph,
            organic_carbon_percent=payload.organic_carbon_percent,
            fym_applied_tons_per_ha=payload.fym_applied_tons_per_ha or 0.0,
            pure_n_req_kg_per_ha=rec.pure_nutrients_recommended_kg_per_ha["N"],
            pure_p2o5_req_kg_per_ha=rec.pure_nutrients_recommended_kg_per_ha["P2O5"],
            pure_k2o_req_kg_per_ha=rec.pure_nutrients_recommended_kg_per_ha["K2O"],
            fertilizer_products=[p.model_dump() for p in rec.commercial_fertilizers],
            split_schedule=[s.model_dump() for s in rec.split_schedule],
            organic_alternatives=[o.model_dump() for o in rec.organic_alternatives],
            weather_adjustment=rec.weather_adjustment.model_dump() if rec.weather_adjustment else None,
            explanation=rec.explanation,
            citations=rec.citations,
            user_confirmed=payload.user_confirmed
        )
        db.add(db_rec)
        await db.commit()
        await db.refresh(db_rec)
        rec.id = db_rec.id
        return rec
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fertilizer recommendation engine error: {str(e)}")


@router.post("/ocr-upload")
async def upload_soil_report_ocr(
    file: UploadFile = File(...)
):
    """
    Upload scanned soil health card image or PDF.
    Extracts soil parameters and prompts farmer for explicit review and confirmation before calculation.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    
    extracted = ocr_service.parse_soil_report_image(contents)
    extracted["filename"] = file.filename
    return extracted


@router.get("/ml-evaluation")
async def get_fertilizer_ml_evaluation():
    """Retrieve Fertilizer ML evaluation report comparing Gradient Boosting against Agronomy Baseline."""
    if not fertilizer_ml.is_trained:
        fertilizer_ml.train_and_evaluate()
    return fertilizer_ml.evaluation_results
