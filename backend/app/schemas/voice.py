from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class VoiceTranscribeRequest(BaseModel):
    audio_base64: Optional[str] = None
    text_transcript: Optional[str] = None # Browser Web Speech transcript input
    language: str = Field("hi", description="Language code: hi, en, sw, am, ha")
    mode: str = Field("advisory_query", description="advisory_query or soil_data_entry")


class ParsedSoilVoiceData(BaseModel):
    soil_n: Optional[float] = None
    soil_p: Optional[float] = None
    soil_k: Optional[float] = None
    soil_ph: Optional[float] = None
    field_area: Optional[float] = None
    area_unit: Optional[str] = None
    crop: Optional[str] = None
    confirmation_sentence: str
    is_complete: bool
    missing_fields: List[str]


class VoiceTranscribeResponse(BaseModel):
    recognized_text: str
    detected_language: str
    parsed_soil_data: Optional[ParsedSoilVoiceData] = None
    response_audio_text: str
    readback_speech: str


class TTSRequest(BaseModel):
    text: str
    language: str = "hi"
