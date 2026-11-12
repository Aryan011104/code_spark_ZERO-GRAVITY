from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatQueryRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Farmer's question")
    crop_context: Optional[str] = Field(None, description="Active crop context (coffee, potato, maize)")
    field_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Active soil/field state")
    conversation_id: Optional[str] = Field(None, description="Session ID for multi-turn history")
    language: str = Field("en", description="User language code (en, hi, sw, am, ha)")


class Citation(BaseModel):
    source_title: str
    section: Optional[str] = None
    page: Optional[int] = None
    region: Optional[str] = None
    publication_year: Optional[int] = None
    url: Optional[str] = None
    excerpt: str


class ChatQueryResponse(BaseModel):
    response: str
    conversation_id: str
    citations: List[Citation]
    detected_intent: str # fertilizer, disease, weather, general_advisory
    failure_category: Optional[str] = None # None, "Out of Context", "Out of Collection", "Out of Content"
    follow_up_suggestions: List[str]
    has_banned_chemical_warning: bool = False
    safety_notes: List[str] = []
