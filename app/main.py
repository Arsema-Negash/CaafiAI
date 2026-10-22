"""CAAFI_AI FastAPI application entry point."""
from fastapi import FastAPI

from app.api.consultation import router as consultation_router

app = FastAPI(
    title="CAAFI_AI",
    description=(
        "Research prototype for retrieving Ethiopian clinical-guideline evidence. "
        "It is not a diagnostic or validated triage system."
    ),
    version="0.1.0",
)

app.include_router(consultation_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Indicate that the API process is responding (not model readiness)."""
    return {"status": "ok", "service": "CAAFI_AI"}


@app.get("/ready", tags=["system"])
def readiness_check() -> dict[str, str | bool]:
    """Check that the generated guideline index exists on disk."""
    from app.ai.retrieval import EMBEDDINGS_FILE

    ready = EMBEDDINGS_FILE.is_file()
    return {
        "ready": ready,
        "clinical_index": "available" if ready else "missing",
    }
