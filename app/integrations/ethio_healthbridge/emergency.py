"""Conservative keyword red-flag checks adapted from Ethio-HealthBridge.

This is a safety prompt, not a validated triage classifier. It never contacts
emergency services. Keyword matching can miss emergencies and can also flag a
negated phrase, so the warning asks the person to seek professional help.
"""
from __future__ import annotations

import re

RED_FLAGS_AMHARIC = (
    "ደረት ህመም",
    "የመተንፈስ ችግር",
    "መሳት",
    "ብዙ ደም",
    "የመናገር ችግር",
    "ድንገተኛ ድክመት",
    "መመረዝ",
    "መቃጠል",
)

RED_FLAGS_ENGLISH = (
    r"\bchest pain\b",
    r"\bdifficulty breathing\b",
    r"\bshortness of breath\b",
    r"\b(can't|cannot) breathe\b",
    r"\bsevere (bleeding|bleed)\b",
    r"\bheavy bleeding\b",
    r"\bunconscious\b",
    r"\bnot waking up\b",
    r"\bsudden weakness\b",
    r"\b(face|arm|leg) drooping\b",
    r"\b(can't|cannot) speak\b",
    r"\bseizure\b",
    r"\bconvulsion\b",
    r"\bpoisoning\b",
    r"\boverdose\b",
)


def detect_red_flag(text: str) -> str | None:
    """Return a matched red-flag phrase, or None; no model/network call occurs."""
    normalized = " ".join(text.lower().replace("፣", " ").replace("።", " ").split())
    for phrase in RED_FLAGS_AMHARIC:
        if phrase in normalized:
            return phrase
    for pattern in RED_FLAGS_ENGLISH:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            # Avoid some obvious English negations, without claiming full NLP.
            before = normalized[max(0, match.start() - 24):match.start()]
            if re.search(r"\b(no|not|without|never)\s+(?:any\s+)?$", before):
                continue
            return match.group(0)
    return None


def emergency_message(language: str = "en") -> str:
    if language == "am":
        return (
            "ማስጠንቀቂያ፦ ይህ አደገኛ ምልክት ሊሆን ይችላል። "
            "እባክዎ አሁኑኑ የአካባቢዎን የአስቸኳይ ሕክምና እርዳታ ያግኙ ወይም ወደ ቅርብ ጤና ተቋም ይሂዱ። "
            "CAAFI_AI ለእርስዎ አይደውልም።"
        )
    return (
        "Safety warning: this symptom may indicate a medical emergency. "
        "Please seek immediate professional medical help or contact your local "
        "emergency service now. CAAFI_AI does not call emergency services for you."
    )
