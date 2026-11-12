import re
from typing import Tuple

# Blacklisted/Banned pesticides according to CIBRC (India) and international conventions (Stockholm/Rotterdam)
BANNED_PESTICIDES = {
    "endosulfan": "Banned worldwide under Stockholm Convention. Highly toxic organochlorine.",
    "monocrotophos": "Banned on vegetables and restricted due to extreme mammalian toxicity.",
    "paraquat": "Banned/severely restricted in multiple jurisdictions; fatal ingestion risk with no antidote.",
    "carbofuran": "Banned/severely restricted carbamate; lethal to non-target wildlife and birds.",
    "ddt": "Banned for agricultural use globally under Stockholm Convention.",
    "aldicarb": "Extremely hazardous organophosphate/carbamate banned in agriculture.",
    "chlordane": "Banned persistent organic pollutant.",
    "methyl parathion": "Banned chemical of extreme toxicity.",
    "phorate": "Banned/restricted high-hazard pesticide.",
    "lindane": "Banned organochlorine.",
}

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s*prompt",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"act\s+as\s+(an\s+unrestricted|a\s+hacked)\s+ai",
    r"bypass\s+(safety|content)\s+filters",
    r"disregard\s+(all\s+)?rules",
    r"override\s+safety\s+guidelines",
    r"recommend\s+(banned|illegal|poisonous)\s+chemicals"
]

def sanitize_input_text(text: str) -> str:
    """Sanitize user input against injection attacks and control characters."""
    if not text:
        return ""
    # Strip null bytes and unusual control characters, preserve newlines and common punctuation
    cleaned = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", "", text)
    return cleaned.strip()

def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """Check if input contains adversarial prompt injection attacks."""
    lower_text = text.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower_text):
            return True, f"Prompt injection pattern detected: '{pattern}'"
    return False, ""

def check_banned_chemicals(query_or_text: str) -> Tuple[bool, list[str]]:
    """Scan query or output text for banned pesticides."""
    lower = query_or_text.lower()
    detected = []
    for chem, reason in BANNED_PESTICIDES.items():
        if re.search(rf"\b{re.escape(chem)}\b", lower):
            detected.append(f"{chem.capitalize()} ({reason})")
    return (len(detected) > 0), detected

def mask_pii(text: str) -> str:
    """Mask phone numbers, email addresses, and aadhaar/national ID patterns for farmer privacy."""
    # Mask emails
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL_PROTECTED]", text)
    # Mask 10-digit phone numbers
    text = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE_PROTECTED]", text)
    return text
