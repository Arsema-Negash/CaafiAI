"""HTTP API for evidence-grounded clinical guideline consultation."""
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.core.ai_engine import generate_health_response

router = APIRouter(tags=["consultation"])


class ConsultationRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000, description="Question or symptom description")
    language: str = Field(default="en", min_length=2, max_length=20)

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
    sources: list[SourceReference]
    disclaimer: str


def _consult(request: ConsultationRequest) -> dict[str, Any]:
    try:
        return generate_health_response(request.message, request.language)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "The clinical guideline index is unavailable. Run the ingestion, "
                "chunking, and embedding build steps before using consultation."
            ),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/chat", response_model=ConsultationResponse, summary="Retrieve guideline evidence")
@router.post("/api/consultation", response_model=ConsultationResponse, include_in_schema=True)
def consultation(request: ConsultationRequest) -> dict[str, Any]:
    """Return source-linked evidence; this endpoint does not diagnose patients."""
    return _consult(request)
