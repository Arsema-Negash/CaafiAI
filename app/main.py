"""CAAFI_AI FastAPI application entry point."""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.consultation import router as consultation_router
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("caafi_ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing startup and shutdown tasks."""
    logger.info(
        "Starting CAAFI_AI service (env=%s, version=%s)...",
        settings.environment,
        settings.version,
    )
    yield
    logger.info("Shutting down CAAFI_AI service.")


app = FastAPI(
    title="CAAFI_AI",
    description=(
        "Research prototype for retrieving Ethiopian clinical-guideline evidence. "
        "It is an informational decision-support prototype and not a diagnostic, "
        "prescriptive, or validated triage system."
    ),
    version=settings.version,
    lifespan=lifespan,
)

app.include_router(consultation_router)


@app.get("/", tags=["system"])
def root_info() -> dict[str, str]:
    """Root endpoint providing service metadata and guidance."""
    return {
        "service": settings.project_name,
        "version": settings.version,
        "docs_url": "/docs",
        "guideline": "Ethiopian Primary Health Care Clinical Guidelines, 2017",
        "notice": "Research prototype for guideline retrieval. Not a medical device or triage tool.",
    }


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
