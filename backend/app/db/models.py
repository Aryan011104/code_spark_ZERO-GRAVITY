from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Boolean
from datetime import datetime, timezone
from backend.app.db.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class FertilizerRecommendation(Base):
    __tablename__ = "fertilizer_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=utcnow)
    farmer_id = Column(String(64), index=True, nullable=True)
    crop = Column(String(64), index=True, nullable=False)
    growth_stage = Column(String(64), nullable=False)
    location = Column(String(128), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Field and soil inputs
    field_area = Column(Float, nullable=False)
    area_unit = Column(String(32), nullable=False)
    area_in_hectares = Column(Float, nullable=False)
    
    soil_n = Column(Float, nullable=False)
    soil_p = Column(Float, nullable=False)
    soil_k = Column(Float, nullable=False)
    nutrient_unit = Column(String(32), default="kg/ha")
    
    soil_ph = Column(Float, nullable=True)
    organic_carbon_percent = Column(Float, nullable=True)
    moisture_status = Column(String(32), nullable=True)
    irrigation_context = Column(String(64), nullable=True)
    
    # Previous applications
    fym_applied_tons_per_ha = Column(Float, default=0.0)
    recent_fertilizers = Column(JSON, nullable=True)
    
    # Recommendations computed
    pure_n_req_kg_per_ha = Column(Float, nullable=False)
    pure_p2o5_req_kg_per_ha = Column(Float, nullable=False)
    pure_k2o_req_kg_per_ha = Column(Float, nullable=False)
    
    fertilizer_products = Column(JSON, nullable=False) # e.g. [{"name": "Urea", "kg_per_ha": 120, "total_kg": 240, ...}]
    split_schedule = Column(JSON, nullable=False)
    organic_alternatives = Column(JSON, nullable=True)
    weather_adjustment = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=False)
    citations = Column(JSON, nullable=False)
    
    user_confirmed = Column(Boolean, default=True)


class DiseaseCase(Base):
    __tablename__ = "disease_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_reference = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    crop = Column(String(64), index=True, nullable=False)
    plant_part = Column(String(64), nullable=False)
    symptoms = Column(JSON, nullable=False)
    symptom_duration_days = Column(Integer, nullable=True)
    growth_stage = Column(String(64), nullable=True)
    location = Column(String(128), nullable=True)
    image_url = Column(String(512), nullable=True)
    
    # Diagnosis evaluation
    image_quality_passed = Column(Boolean, default=True)
    quality_notes = Column(String(256), nullable=True)
    
    primary_condition = Column(String(128), nullable=False)
    condition_type = Column(String(64), nullable=False) # disease, pest, deficiency, environmental, healthy
    calibrated_confidence = Column(Float, nullable=False)
    is_inconclusive = Column(Boolean, default=False)
    
    alternative_causes = Column(JSON, nullable=True)
    supporting_observations = Column(JSON, nullable=True)
    ipm_measures = Column(JSON, nullable=False)
    follow_up_questions = Column(JSON, nullable=True)
    expert_referral = Column(JSON, nullable=True)


class RAGDocumentChunk(Base):
    __tablename__ = "rag_document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(128), index=True)
    title = Column(String(256), nullable=False)
    section = Column(String(256), nullable=True)
    page_number = Column(Integer, nullable=True)
    region = Column(String(128), nullable=True)
    publication_year = Column(Integer, nullable=True)
    url = Column(String(512), nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True) # Stored as JSON float list for SQLite and compatible with pgvector


class CallSession(Base):
    __tablename__ = "telephony_call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    call_sid = Column(String(128), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    caller_number = Column(String(64), nullable=True)
    language = Column(String(16), default="hi")
    current_step = Column(String(64), default="WELCOME")
    session_data = Column(JSON, default=dict)
    consultation_ref = Column(String(64), index=True, nullable=True)
    status = Column(String(32), default="in_progress")


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=utcnow)
    service = Column(String(64), nullable=False) # fertilizer, disease, chat, ivr
    reference_id = Column(String(64), nullable=True)
    rating = Column(Integer, nullable=False) # 1 to 5
    comments = Column(Text, nullable=True)
