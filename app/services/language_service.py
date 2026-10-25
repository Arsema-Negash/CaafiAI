"""Language detection and translation for bilingual clinical queries.

Supports English (en) and Amharic (am) as primary languages.
Amharic queries are translated to English for retrieval, then
responses are optionally translated back.

Falls back gracefully to English if translation services fail.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("caafi_ai.language")

SUPPORTED_LANGUAGES = frozenset(["en", "am"])
LANGUAGE_NAMES = {"en": "English", "am": "Amharic (አማርኛ)"}


def detect_language(text: str) -> str:
    """Detect the language of a text string.

    Returns an ISO 639-1 code: 'en', 'am', or 'en' as fallback.
    Never raises — returns 'en' on any error.
    """
    try:
        from langdetect import detect, LangDetectException
        lang = detect(text)
        # Normalize: langdetect returns 'am' for Amharic
        if lang in SUPPORTED_LANGUAGES:
            return lang
        logger.info("Detected unsupported language '%s', defaulting to 'en'.", lang)
        return "en"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Language detection failed: %s", type(exc).__name__)
        return "en"


def translate_to_english(text: str, source_language: str = "am") -> str:
    """Translate text from source_language to English.

    Uses deep-translator (free, no API key required).
    Falls back to the original text on failure.
    """
    if source_language == "en":
        return text
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=source_language, target="en")
        result = translator.translate(text)
        logger.info("Translated query from %s to en.", source_language)
        return result or text
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Translation %s->en failed (%s), using original text.",
            source_language,
            type(exc).__name__,
        )
        return text


def translate_from_english(text: str, target_language: str = "am") -> str:
    """Translate an English response to target_language.

    Falls back to English on failure.
    """
    if target_language == "en":
        return text
    try:
        from deep_translator import GoogleTranslator
        # deep_translator has a chunk limit; split long texts
        MAX_CHARS = 4500
        if len(text) <= MAX_CHARS:
            translator = GoogleTranslator(source="en", target=target_language)
            result = translator.translate(text)
            return result or text
        # Translate in paragraphs
        paragraphs = text.split("\n\n")
        translated_parts = []
        for para in paragraphs:
            if para.strip():
                translator = GoogleTranslator(source="en", target=target_language)
                t = translator.translate(para[:MAX_CHARS])
                translated_parts.append(t or para)
            else:
                translated_parts.append("")
        logger.info("Translated response from en to %s.", target_language)
        return "\n\n".join(translated_parts)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Translation en->%s failed (%s), returning English.",
            target_language,
            type(exc).__name__,
        )
        return text
