"""Voice I/O service: Speech-to-Text (Whisper) and Text-to-Speech (gTTS).

Whisper transcribes audio files to text. gTTS converts text to speech.
Both run locally with no API keys. Whisper downloads its model on first use.

Supported audio formats: mp3, mp4, wav, m4a, ogg, flac, webm.
"""
from __future__ import annotations

import io
import logging
import os
import tempfile
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger("caafi_ai.voice")

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium
SUPPORTED_AUDIO_FORMATS = frozenset(["mp3", "mp4", "wav", "m4a", "ogg", "flac", "webm"])


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """Transcribe audio bytes to text using OpenAI Whisper (local).

    Downloads the Whisper model on first call (~150MB for 'base').
    Returns the transcribed text.
    Raises RuntimeError on failure.
    """
    ext = Path(filename).suffix.lstrip(".").lower()
    if ext not in SUPPORTED_AUDIO_FORMATS:
        raise ValueError(f"Unsupported audio format: {ext}. Supported: {SUPPORTED_AUDIO_FORMATS}")

    try:
        import whisper
    except ImportError as exc:
        raise RuntimeError(
            "openai-whisper is not installed. Run: pip install openai-whisper"
        ) from exc

    try:
        model = whisper.load_model(WHISPER_MODEL_SIZE)
    except Exception as exc:
        raise RuntimeError(f"Failed to load Whisper model '{WHISPER_MODEL_SIZE}': {exc}") from exc

    # Write bytes to a temporary file (whisper requires a file path)
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = model.transcribe(tmp_path)
        text = result.get("text", "").strip()
        logger.info("Whisper transcription complete: chars=%d", len(text))
        return text
    except Exception as exc:
        raise RuntimeError(f"Whisper transcription failed: {exc}") from exc
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def text_to_speech(text: str, language: str = "en") -> bytes:
    """Convert text to speech audio bytes (MP3) using gTTS.

    Supports 'en' (English) and 'am' (Amharic).
    Returns raw MP3 bytes.
    Raises RuntimeError on failure.
    """
    # Map language codes to gTTS codes
    lang_map = {
        "en": "en",
        "am": "am",  # gTTS supports Amharic
    }
    gtts_lang = lang_map.get(language, "en")

    try:
        from gtts import gTTS
    except ImportError as exc:
        raise RuntimeError("gTTS is not installed. Run: pip install gTTS") from exc

    try:
        # Truncate very long text for TTS (gTTS has limits)
        max_tts_chars = 2000
        tts_text = text[:max_tts_chars]
        if len(text) > max_tts_chars:
            tts_text += "..."

        tts = gTTS(text=tts_text, lang=gtts_lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_bytes = audio_buffer.read()
        logger.info("TTS generated: lang=%s, bytes=%d", gtts_lang, len(audio_bytes))
        return audio_bytes
    except Exception as exc:
        raise RuntimeError(f"TTS generation failed: {exc}") from exc
