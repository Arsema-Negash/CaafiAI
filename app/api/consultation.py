"""HTTP API for evidence-grounded clinical guideline consultation."""
from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.core.ai_engine import generate_health_response
from app.core.config import settings

logger = logging.getLogger("caafi_ai.consultation")

router = APIRouter(tags=["consultation"])


class ConsultationRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=settings.max_message_length,
        description="Clinical inquiry or symptom description to retrieve evidence for",
    )
    language: str = Field(
        default="en",
        min_length=2,
        max_length=20,
        description="Language code for the response (currently 'en' supported)",
    )

    @field_validator("language")
    @classmethod
    def english_only_for_mvp(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized != "en":
            raise ValueError("Only English responses are supported in this MVP.")
        return normalized

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be blank.")
        return value.strip()


class SourceReference(BaseModel):
    id: int | str | None = None
    topic: str | None = None
    population: str | None = None
    page: int | str | None = None
    source: str | None = None
    content: str
    similarity: float


class ConsultationResponse(BaseModel):
    response: str
    language: str
    severity: str
    urgent: bool | None
    evidence_status: str
    sources: list[SourceReference]
    disclaimer: str


def _consult(request: ConsultationRequest) -> dict[str, Any]:
    # Privacy safeguard: Log message length and language only, NEVER patient text.
    logger.info(
        "Processing consultation request: language=%s, query_chars=%d",
        request.language,
        len(request.message),
    )
    start_time = time.perf_counter()
    try:
        result = generate_health_response(request.message, request.language)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "Consultation completed: retrieved_sources=%d, duration_ms=%.1f",
            len(result.get("sources", [])),
            elapsed_ms,
        )
        return result
    except FileNotFoundError as exc:
        logger.warning("Clinical guideline index is unavailable.")
        raise HTTPException(
            status_code=503,
            detail=(
                "The clinical guideline index is unavailable. Run the ingestion, "
                "chunking, and embedding build steps before using consultation."
            ),
        ) from exc
    except RuntimeError as exc:
        logger.error("Runtime error during consultation: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="The retrieval service is temporarily unavailable.",
        ) from exc
    except ValueError as exc:
        logger.warning("Validation error during consultation: %s", type(exc).__name__)
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/chat", response_model=ConsultationResponse, summary="Retrieve guideline evidence")
@router.post("/api/consultation", response_model=ConsultationResponse, include_in_schema=True)
def consultation(request: ConsultationRequest) -> dict[str, Any]:
    """Return source-linked evidence; this endpoint does not diagnose patients."""
    return _consult(request)
