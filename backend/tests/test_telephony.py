import pytest
from backend.app.schemas.telephony import TelephonyWebhookRequest
from backend.app.services.telephony_service import telephony_service

@pytest.mark.asyncio
async def test_full_ivr_call_session_flow():
    """Simulate a complete incoming telephone consultation over DTMF keypad."""
    call_sid = "TEST-CALL-SID-99"

    # Turn 1: Welcome & Language selection -> Farmer presses 1 for Hindi
    t1 = await telephony_service.handle_call_turn(TelephonyWebhookRequest(CallSid=call_sid, Digits="1"))
    assert t1.next_step == "MAIN_MENU"
    assert "खाद की मात्रा" in t1.prompt_text

    # Turn 2: Main Menu -> Farmer presses 1 for Fertilizer
    t2 = await telephony_service.handle_call_turn(TelephonyWebhookRequest(CallSid=call_sid, Digits="1"))
    assert t2.next_step == "CROP_SELECT"
    assert "फसल चुनें" in t2.prompt_text

    # Turn 3: Crop Selection -> Farmer presses 2 for Potato
    t3 = await telephony_service.handle_call_turn(TelephonyWebhookRequest(CallSid=call_sid, Digits="2"))
    assert t3.next_step == "AREA_ENTRY"
    assert "potato" in t3.prompt_text.lower() or "आलू" in t3.prompt_text

    # Turn 4: Area Entry -> Farmer enters '2#' (2 acres)
    t4 = await telephony_service.handle_call_turn(TelephonyWebhookRequest(CallSid=call_sid, Digits="2#"))
    assert t4.next_step == "ADVICE_RESULT"
    assert t4.session_status == "completed"
    assert "डीएपी" in t4.prompt_text or "यूरिया" in t4.prompt_text
    assert t4.consultation_ref is not None
    assert t4.consultation_ref.startswith("TEL-")
