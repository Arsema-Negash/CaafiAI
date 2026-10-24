"""Evidence-first consultation orchestration for the CAAFI_AI MVP.

This module intentionally does not claim to diagnose or perform clinical triage.
It returns retrieved guideline passages with source metadata for human review.
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

    if not sources:
        response = (
            "I could not retrieve a relevant passage from the currently loaded "
            "clinical guideline. Do not treat this as evidence that no risk exists."
        )
    else:
        response = (
            f"I retrieved {len(sources)} potentially relevant passage(s) from "
            "the clinical guideline. These are evidence excerpts, not a diagnosis "
            "or a validated triage decision. Review the source and page references "
            "below with a qualified health professional."
        )

    return {
        "response": response,
        "language": language,
        "severity": "not_assessed",
        "urgent": None,
        "sources": sources,
        "disclaimer": DISCLAIMER,
    }
