from fastapi import APIRouter, Response, Request, Header
from typing import Optional
from backend.app.schemas.telephony import (
    TelephonyWebhookRequest,
    TelephonyActionResponse,
    SimulatorDialRequest
)
from backend.app.services.telephony_service import telephony_service, CALL_SESSIONS

router = APIRouter()

@router.post("/webhook")
async def telephony_incoming_webhook(
    request: Request,
    x_twilio_signature: Optional[str] = Header(None)
):
    """
    Standardized Telephony Webhook for incoming voice calls.
    Accepts form-urlencoded or JSON payload from Twilio / Africa's Talking / Asterisk.
    Returns TwiML / XML audio responses.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "SIMULATED-CALL-01")
    digits = form_data.get("Digits", None)
    caller = form_data.get("From", "+919876543210")
    
    webhook_req = TelephonyWebhookRequest(
        CallSid=call_sid,
        From=caller,
        Digits=digits
    )
    action_res = await telephony_service.handle_call_turn(webhook_req)
    return Response(content=action_res.twiml_or_xml, media_type="application/xml")


@router.post("/simulator/dial", response_model=TelephonyActionResponse)
async def simulate_ivr_keypad_dial(req: SimulatorDialRequest):
    """
    Interactive local IVR simulator endpoint.
    Allows web UI or CLI users to simulate dialing numbers, entering DTMF digits,
    and listening to real backend fertilizer / disease consultations.
    """
    webhook_req = TelephonyWebhookRequest(
        CallSid=req.call_sid,
        Digits=req.digits
    )
    return await telephony_service.handle_call_turn(webhook_req)


@router.get("/simulator/session/{call_sid}")
async def get_simulator_session_state(call_sid: str):
    """Inspect active IVR call session state, entered variables, and consultation reference."""
    session = CALL_SESSIONS.get(call_sid)
    if not session:
        return {"status": "not_found", "call_sid": call_sid}
    return {
        "call_sid": session["call_sid"],
        "caller_phone": session["caller_phone"],
        "current_step": session["current_step"],
        "language": session["language"],
        "data": session["data"],
        "consultation_ref": session["data"].get("case_ref")
    }
