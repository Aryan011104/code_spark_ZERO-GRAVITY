from fastapi import APIRouter, HTTPException
from backend.app.schemas.rag import ChatQueryRequest, ChatQueryResponse
from backend.app.services.rag_service import rag_service

router = APIRouter()

@router.post("/query", response_model=ChatQueryResponse)
async def chat_with_agri_assistant(req: ChatQueryRequest):
    """
    Agricultural RAG Chatbot query endpoint grounded in verified agronomy literature.
    Returns grounded advice, verified citations, prompt injection checks, and failure categories.
    """
    try:
        return await rag_service.answer_query(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG Chatbot error: {str(e)}")
