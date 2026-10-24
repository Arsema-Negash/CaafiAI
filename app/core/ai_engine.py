"""Evidence-first consultation orchestration for the CAAFI_AI MVP.

This module intentionally does not claim to diagnose or perform clinical triage.
It returns retrieved guideline passages with source metadata for human review.
Answers are extractive: every quoted sentence comes from a retrieved chunk.
"""
from typing import Any

from app.ai.retrieval import search_clinical_guidelines
from app.core.config import settings


DISCLAIMER = (
    "CAAFI_AI is an early research prototype, not a medical professional. "
    "It does not diagnose conditions or assess clinical urgency. Verify the "
    "guideline excerpts with a qualified health professional. If someone may "
    "be in immediate danger, seek urgent medical care."
)

EXCERPT_CHAR_LIMIT = 480


def _excerpt(content: str) -> str:
    """Return a single-line excerpt that is a prefix of the source chunk only."""
    collapsed = " ".join(content.split())
    if len(collapsed) <= EXCERPT_CHAR_LIMIT:
        return collapsed
    return collapsed[: EXCERPT_CHAR_LIMIT].rstrip() + "…"


def compose_extractive_response(sources: list[dict[str, Any]]) -> str:
    """Quote retrieved passages. Do not add clinical claims that are not in the sources."""
    if not sources:
        return (
            "I could not retrieve a relevant passage from the currently loaded "
            "clinical guideline. Do not treat this as evidence that no risk exists."
        )

    lines = [
        (
            f"I retrieved {len(sources)} potentially relevant passage(s) from "
            "the clinical guideline. These are evidence excerpts, not a diagnosis "
            "or a validated triage decision. Review the source and page references "
            "below with a qualified health professional."
        ),
        "",
        "Quoted excerpts (text is copied from retrieved chunks only):",
    ]
    for index, source in enumerate(sources, start=1):
        topic = source.get("topic") or "Unknown topic"
        population = source.get("population") or "Unspecified population"
        page = source.get("page")
        page_label = "page unknown" if page in (None, "") else f"page {page}"
        lines.append(
            f"{index}. [{topic} | {population} | {page_label}] {_excerpt(source.get('content') or '')}"
        )
    return "\n".join(lines)


def generate_health_response(message: str, language: str = "en") -> dict[str, Any]:
    """Return retrieved guideline evidence without fabricating a diagnosis."""
    query = message.strip()
    if not query:
        raise ValueError("Message cannot be empty.")

    results = search_clinical_guidelines(query, top_k=settings.default_top_k)
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

    return {
        "response": compose_extractive_response(sources),
        "language": language,
        "severity": "not_assessed",
        "urgent": None,
        "sources": sources,
        "disclaimer": DISCLAIMER,
    }
