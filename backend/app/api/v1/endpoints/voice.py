from fastapi import APIRouter
from backend.app.schemas.voice import VoiceTranscribeRequest, VoiceTranscribeResponse
from backend.app.services.voice_service import voice_service

router = APIRouter()

@router.post("/process", response_model=VoiceTranscribeResponse)
async def process_voice_input(req: VoiceTranscribeRequest):
    """Process spoken agricultural advisory questions or spoken soil-data entry with voice readback."""
    return voice_service.process_voice_interaction(req)

@router.get("/languages")
async def get_language_coverage():
    """Return multilingual support matrix (Hindi, English, Swahili, Amharic, Hausa)."""
    return voice_service.get_supported_languages()
