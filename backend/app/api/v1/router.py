from fastapi import APIRouter
from backend.app.api.v1.endpoints import fertilizer, disease, chat, voice, telephony, evaluations

api_router = APIRouter()

api_router.include_router(fertilizer.router, prefix="/fertilizer", tags=["Fertilizer Recommendations"])
api_router.include_router(disease.router, prefix="/disease", tags=["Crop Disease Assessment"])
api_router.include_router(chat.router, prefix="/chat", tags=["Grounded RAG Chatbot"])
api_router.include_router(voice.router, prefix="/voice", tags=["Multilingual Voice"])
api_router.include_router(telephony.router, prefix="/telephony", tags=["Telephony & IVR"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["Benchmarks & Reports"])
