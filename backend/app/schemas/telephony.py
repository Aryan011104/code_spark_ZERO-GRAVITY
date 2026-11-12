from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class TelephonyWebhookRequest(BaseModel):
    CallSid: str = Field(..., description="Unique call identifier from provider")
    From: Optional[str] = Field("+919876543210", description="Caller phone number")
    Digits: Optional[str] = Field(None, description="DTMF keypresses entered by caller")
    SpeechResult: Optional[str] = Field(None, description="Spoken speech transcribed by provider")
    CallStatus: Optional[str] = Field("in-progress", description="ringing, in-progress, completed")


class TelephonyActionResponse(BaseModel):
    twiml_or_xml: str
    prompt_text: str
    audio_url: Optional[str] = None
    consultation_ref: Optional[str] = None
    next_step: str
    session_status: str


class SimulatorDialRequest(BaseModel):
    call_sid: str = Field(..., description="Simulated call ID")
    digits: Optional[str] = Field(None, description="Keypad input (0-9, *, #)")
    language: Optional[str] = Field(None, description="Active language selection")
    action_type: str = Field("keypad", description="keypad, speech, hangup")
