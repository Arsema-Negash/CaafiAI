"""Amharic audio transcription adapted from Ethio-HealthBridge's Gemini STT."""
from __future__ import annotations

import os
import re
from pathlib import Path


def clean_for_retrieval(text: str) -> str:
    """Normalize common Amharic character variants without inventing content."""
    if not text:
        return ""
    text = re.sub("[ሃኅኃሐሓኻ]", "ሀ", text)
    text = re.sub("[ሐሑሒሓሔሕሖ]", "ሀ", text)
    text = re.sub("[ኈኊኋኌኍ]", "ሁ", text)
    text = re.sub("[ሠ]", "ሰ", text)
    text = re.sub("[ዓኣዐ]", "አ", text)
    text = re.sub("[ጸፀ]", "ጸ", text)
    return " ".join(text.split())


def transcribe_audio(audio_path: str, language: str = "am") -> str:
    """Transcribe a browser-recorded audio file using Gemini; fail explicitly."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY in your local .env to enable Amharic voice transcription.")
    if not Path(audio_path).is_file():
        raise FileNotFoundError("The uploaded audio file could not be read.")

    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError("google-generativeai is not installed. Install the project requirements.") from exc

    uploaded = None
    try:
        genai.configure(api_key=api_key)
        uploaded = genai.upload_file(path=audio_path)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"))
        response = model.generate_content(
            [
                (
                    "Transcribe the speech in this audio exactly as spoken in Amharic script. "
                    "Do not translate, summarize, or add words. Return only the transcript. "
                    "If speech is not intelligible, return an empty string."
                    if language == "am" else
                    "Transcribe the speech in this audio exactly as spoken in English. "
                    "Do not translate, summarize, or add words. Return only the transcript. "
                    "If speech is not intelligible, return an empty string."
                ),
                uploaded,
            ],
            generation_config=genai.GenerationConfig(temperature=0.0, top_p=1, top_k=1),
        )
        transcript = (getattr(response, "text", "") or "").strip()
        if language == "am":
            transcript = clean_for_retrieval(transcript)
        if not transcript:
            raise RuntimeError("No intelligible speech was returned by the transcription service. Please try again or type your question.")
        return transcript
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("Audio transcription failed. Check the Gemini API key, internet connection, and service quota.") from exc
    finally:
        if uploaded is not None:
            try:
                genai.delete_file(uploaded.name)
            except Exception:
                pass
