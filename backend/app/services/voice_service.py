import re
from typing import Dict, Any, List, Optional
from backend.app.schemas.voice import (
    VoiceTranscribeRequest,
    VoiceTranscribeResponse,
    ParsedSoilVoiceData
)

# Supported Language Matrix & Provider Architecture
LANGUAGE_PROVIDERS = {
    "hi": {
        "name": "Hindi (हिंदी)",
        "locale": "hi-IN",
        "status": "LIVE_DEMONSTRATED",
        "stt_engine": "WebSpeechAPI + Backend Phonetic Normalizer",
        "tts_engine": "Native SpeechSynthesis (hi-IN) with fallback audio generator",
        "description": "Full end-to-end voice query and soil-data spoken entry demonstrated."
    },
    "en": {
        "name": "English (Indian/International)",
        "locale": "en-IN",
        "status": "LIVE_DEMONSTRATED",
        "stt_engine": "WebSpeechAPI + Native Speech Engine",
        "tts_engine": "Native SpeechSynthesis (en-IN / en-US)",
        "description": "Full end-to-end advisory and soil test spoken entry demonstrated."
    },
    "sw": {
        "name": "Swahili (Kiswahili)",
        "locale": "sw-KE",
        "status": "PROVIDER_READY (Staged)",
        "stt_engine": "Africa's Talking / Google Cloud Speech Adapter (sw-KE)",
        "tts_engine": "eSpeak-NG / Cloud TTS Swahili Voice",
        "description": "Provider pipeline configured; live demonstration subject to external cloud API keys."
    },
    "am": {
        "name": "Amharic (አማርኛ)",
        "locale": "am-ET",
        "status": "PROVIDER_READY (Staged)",
        "stt_engine": "Google Cloud Speech / Whisper Amharic Fine-tune",
        "tts_engine": "Cloud TTS Amharic Female Voice",
        "description": "Provider adapter interface ready; live speech requires external cloud credentials."
    },
    "ha": {
        "name": "Hausa",
        "locale": "ha-NG",
        "status": "PROVIDER_READY (Staged)",
        "stt_engine": "Google Cloud Speech / Mozilla CommonVoice Hausa",
        "tts_engine": "Cloud TTS Hausa Voice",
        "description": "Provider adapter interface ready; live speech requires external cloud credentials."
    }
}

class MultilingualVoiceService:
    def get_supported_languages(self) -> Dict[str, Any]:
        """Return full language matrix with explicit live vs provider-ready status."""
        return LANGUAGE_PROVIDERS

    def parse_spoken_soil_data(self, spoken_text: str, language: str = "hi") -> ParsedSoilVoiceData:
        """
        Extract numeric soil parameters from farmer's speech in Hindi or English:
        Example Hindi: "Mera nitrogen 180 hai, phosphorus 20 hai, potash 130 aur khet 2 acre hai"
        Example English: "My nitrogen is 210, phosphorus 25, potash 140, area 1.5 hectares for potato"
        Preserves critical numbers, units, and chemical entities accurately.
        """
        text = spoken_text.lower()
        
        # Numbers extraction
        data = {
            "soil_n": None,
            "soil_p": None,
            "soil_k": None,
            "soil_ph": None,
            "field_area": None,
            "area_unit": "acres",
            "crop": None
        }

        # Crop recognition
        for c in ["coffee", "कॉफ़ी", "काफी"]:
            if c in text:
                data["crop"] = "coffee"
                break
        for c in ["potato", "आलू", "aalu"]:
            if c in text:
                data["crop"] = "potato"
                break
        for c in ["maize", "corn", "मक्का", "makka", "bhutta"]:
            if c in text:
                data["crop"] = "maize"
                break

        # Area extraction (e.g. "2 acre", "1.5 hectare", "20 guntha")
        area_match = re.search(r"(\d+(?:\.\d+)?)\s*(acre|एकड़|hectare|हेक्टेयर|ha|guntha|गुंठा|gunta)", text)
        if area_match:
            data["field_area"] = float(area_match.group(1))
            unit_str = area_match.group(2)
            if "हेक्टेयर" in unit_str or "hectare" in unit_str or "ha" in unit_str:
                data["area_unit"] = "hectares"
            elif "गुंठा" in unit_str or "guntha" in unit_str or "gunta" in unit_str:
                data["area_unit"] = "guntas"
            else:
                data["area_unit"] = "acres"

        # Nitrogen (e.g. "nitrogen 180" or "नाइट्रोजन 180")
        n_match = re.search(r"(?:nitrogen|नाइट्रोजन|\bN\b)\s*(?:hai|is|=|:)?\s*(\d{2,4}(?:\.\d+)?)", text)
        if n_match:
            data["soil_n"] = float(n_match.group(1))

        # Phosphorus (e.g. "phosphorus 22" or "फास्फोरस 25")
        p_match = re.search(r"(?:phosphorus|phosphate|फास्फोरस|\bP\b)\s*(?:hai|is|=|:)?\s*(\d{1,3}(?:\.\d+)?)", text)
        if p_match:
            data["soil_p"] = float(p_match.group(1))

        # Potassium (e.g. "potash 140" or "पोटाश 150")
        k_match = re.search(r"(?:potash|potassium|पोटाश|\bK\b)\s*(?:hai|is|=|:)?\s*(\d{2,4}(?:\.\d+)?)", text)
        if k_match:
            data["soil_k"] = float(k_match.group(1))

        # pH (e.g. "ph 6.5" or "पीएच 6.5")
        ph_match = re.search(r"(?:ph|पीएच)\s*(?:hai|is|=|:)?\s*(\d(?:\.\d+)?)", text)
        if ph_match:
            val = float(ph_match.group(1))
            if 3.0 <= val <= 10.0:
                data["soil_ph"] = val

        # Check missing fields
        missing = []
        if data["soil_n"] is None: missing.append("Nitrogen (N)")
        if data["soil_p"] is None: missing.append("Phosphorus (P)")
        if data["soil_k"] is None: missing.append("Potassium (K)")
        if data["field_area"] is None: missing.append("Field Area")
        if data["crop"] is None: missing.append("Crop Type")

        is_complete = len(missing) == 0

        # Construct voice readback sentence in requested language
        if language == "hi":
            confirm_sentence = (
                f"कृपया पुष्टि करें: फसल {data['crop'] or 'अनिर्धारित'}, क्षेत्रफल {data['field_area'] or 0} {data['area_unit']}, "
                f"नाइट्रोजन {data['soil_n'] or 0} किलोग्राम, फास्फोरस {data['soil_p'] or 0} किलोग्राम, "
                f"पोटाश {data['soil_k'] or 0} किलोग्राम प्रति हेक्टेयर दर्ज किया गया है। क्या यह सही है?"
            )
        else:
            confirm_sentence = (
                f"Please confirm: Crop {data['crop'] or 'unspecified'}, Area {data['field_area'] or 0} {data['area_unit']}, "
                f"Nitrogen {data['soil_n'] or 0} kg/ha, Phosphorus {data['soil_p'] or 0} kg/ha, "
                f"and Potassium {data['soil_k'] or 0} kg/ha. Is this correct?"
            )

        return ParsedSoilVoiceData(
            soil_n=data["soil_n"],
            soil_p=data["soil_p"],
            soil_k=data["soil_k"],
            soil_ph=data["soil_ph"],
            field_area=data["field_area"],
            area_unit=data["area_unit"],
            crop=data["crop"],
            confirmation_sentence=confirm_sentence,
            is_complete=is_complete,
            missing_fields=missing
        )

    def process_voice_interaction(self, req: VoiceTranscribeRequest) -> VoiceTranscribeResponse:
        """Handle voice transcript or speech synthesis generation."""
        spoken = (req.text_transcript or "").strip()
        lang = req.language or "hi"
        
        parsed_soil = None
        if req.mode == "soil_data_entry":
            parsed_soil = self.parse_spoken_soil_data(spoken, language=lang)
            readback = parsed_soil.confirmation_sentence
            resp_audio_text = readback
        else:
            # Advisory voice response
            readback = (
                f"आपकी आवाज सुनी गई: '{spoken}'. सलाहकार उत्तर तैयार किया जा रहा है।"
                if lang == "hi" else
                f"Voice query recognized: '{spoken}'. Generating advisory response."
            )
            resp_audio_text = readback

        return VoiceTranscribeResponse(
            recognized_text=spoken,
            detected_language=lang,
            parsed_soil_data=parsed_soil,
            response_audio_text=resp_audio_text,
            readback_speech=readback
        )

voice_service = MultilingualVoiceService()
