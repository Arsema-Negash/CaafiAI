"""Speech synthesis adapted from Ethio-HealthBridge's edge-tts/gTTS pipeline."""
from __future__ import annotations

import asyncio
import os
import re
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
AUDIO_DIR = PROJECT_ROOT / "data" / "audio_outputs"


def _clean_text(text: str) -> str:
    text = re.sub(r"[*#_]", "", text)
    return re.sub(r"\s+", " ", text).strip()


async def generate_voice_response(text: str, language: str = "am") -> str:
    """Return a generated MP3 path, or an empty string if both TTS providers fail."""
    if not text.strip():
        return ""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    output_path = AUDIO_DIR / f"response_{uuid.uuid4().hex}.mp3"
    cleaned = _clean_text(text[:2000])

    try:
        import edge_tts
        voice = "am-ET-MekdesNeural" if language == "am" else "en-US-JennyNeural"
        await edge_tts.Communicate(cleaned, voice).save(str(output_path))
        if output_path.is_file() and output_path.stat().st_size:
            return str(output_path)
    except Exception:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass

    try:
        from gtts import gTTS
        # gTTS's Amharic support depends on the provider; this fallback is best-effort.
        lang = "am" if language == "am" else "en"
        await asyncio.to_thread(gTTS(text=cleaned, lang=lang, slow=False).save, str(output_path))
        if output_path.is_file() and output_path.stat().st_size:
            return str(output_path)
    except Exception:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
    return ""
