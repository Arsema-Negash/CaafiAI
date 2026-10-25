"""Evidence-grounded consultation orchestration for CAAFI_AI."""
from __future__ import annotations

from typing import Any

from app.ai.generator import (
    GenerationUnavailableError,
    generate_grounded_response,
    generated_response_passes_basic_grounding_checks,
    translate_amharic_query_to_english,
)
from app.ai.retrieval import search_clinical_guidelines
from app.core.config import settings
from app.integrations.ethio_healthbridge.emergency import detect_red_flag, emergency_message

DISCLAIMER = (
    "CAAFI_AI is an experimental research prototype, not a medical professional "
    "or clinically validated service. It does not diagnose or prescribe. Verify "
    "guideline information with a qualified health professional. If someone may "
    "be in immediate danger, seek urgent medical care."
)
EXCERPT_CHAR_LIMIT = 480


def _excerpt(content: str) -> str:
    collapsed = " ".join(content.split())
    if len(collapsed) <= EXCERPT_CHAR_LIMIT:
        return collapsed
    return collapsed[:EXCERPT_CHAR_LIMIT].rstrip() + "…"


def compose_extractive_response(sources: list[dict[str, Any]]) -> str:
    """No model configured? Return labelled source excerpts rather than inventing an answer."""
    if not sources:
        return (
            "I could not retrieve a sufficiently relevant passage from the currently loaded "
            "clinical guideline. This does not mean that no risk exists. Please consult "
            "a qualified health professional."
        )
    lines = [
        f"I found {len(sources)} potentially relevant guideline passage(s). These excerpts are not a diagnosis; "
        "review them with a qualified health professional.",
        "",
        "Evidence excerpts (copied from retrieved guideline text):",
    ]
    for index, source in enumerate(sources, start=1):
        topic = source.get("topic") or "Unknown topic"
        population = source.get("population") or "Unspecified population"
        page = source.get("page")
        page_label = "page unknown" if page in (None, "") else f"page {page}"
        lines.append(f"{index}. [{topic} | {population} | {page_label}] {_excerpt(source.get('content') or '')}")
    return "\n".join(lines)


def generate_health_response(
    message: str,
    language: str = "en",
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Retrieve guideline evidence, short-circuit red flags, and optionally generate grounded prose."""
    query = message.strip()
    if not query:
        raise ValueError("Message cannot be empty.")

    # This local keyword check intentionally runs before retrieval or any LLM call.
    red_flag = detect_red_flag(query)
    if red_flag:
        return {
            "response": emergency_message(language),
            "language": language,
            "severity": "possible_emergency_red_flag",
            "urgent": True,
            "evidence_status": "safety_rule_triggered",
            "sources": [],
            "disclaimer": DISCLAIMER,
            "generation_mode": "local_safety_rule",
            "red_flag": red_flag,
        }

    retrieval_query = query
    prior_user_turns = [
        str(turn.get("content", "")).strip()
        for turn in (history or [])[-6:]
        if turn.get("role") == "user" and str(turn.get("content", "")).strip()
    ]
    if language == "am":
        # Translate the current turn with its prior user context so short Amharic
        # follow-ups remain understandable to the English-only guideline index.
        translation_input = "\n".join(prior_user_turns[-2:] + [query])
        retrieval_query = translate_amharic_query_to_english(translation_input)
        if not settings.gemini_api_key:
            raise GenerationUnavailableError("Amharic consultation requires GEMINI_API_KEY.")
    elif prior_user_turns:
        # Give retrieval context for English follow-ups such as "what about children?".
        retrieval_query = " ".join(prior_user_turns[-2:] + [retrieval_query])

    results = search_clinical_guidelines(retrieval_query, top_k=settings.default_top_k)
    sources = [
        {
            "id": result.get("id"),
            "topic": result.get("topic"),
            "population": result.get("population"),
            "page": result.get("page"),
            "source": result.get("source"),
            "content": result.get("content", ""),
            "similarity": round(float(result.get("score", 0.0)), 4),
        }
        for result in results
    ]

    response_text = compose_extractive_response(sources)
    generation_mode = "extractive_fallback"
    if sources:
        try:
            generated = generate_grounded_response(query, sources, language, history)
            if (
                generated
                and generated.get("response", "").strip()
                and generated_response_passes_basic_grounding_checks(generated["response"], sources)
            ):
                response_text = generated["response"].strip()
                generation_mode = "gemini_grounded"
        except GenerationUnavailableError:
            # English typed fallback remains usable without credentials. For Amharic,
            # an English extractive answer would be misleading, so fail explicitly.
            if language == "am":
                raise
        except Exception:
            # External generation outages do not erase already retrieved evidence.
            if language == "am":
                raise GenerationUnavailableError("Amharic answer generation failed; please try again or use English.")

    return {
        "response": response_text,
        "language": language,
        "severity": "not_assessed",
        "urgent": None,
        "evidence_status": "retrieved" if sources else "insufficient",
        "sources": sources,
        "disclaimer": DISCLAIMER,
        "generation_mode": generation_mode,
    }
