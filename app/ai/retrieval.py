import json
from pathlib import Path
from typing import Any

import numpy as np

from app.ai.embeddings import get_model
from app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMBEDDINGS_FILE = settings.embeddings_path


_cached_chunks: list[dict] | None = None
_cached_file: Path | None = None
_cached_mtime: float | None = None


def parse_embeddings_payload(raw: object) -> tuple[list[dict], dict[str, Any]]:
    """Accept the legacy JSON list and the versioned object wrapper."""
    if isinstance(raw, list):
        return raw, {
            "index_format_version": 0,
            "embedding_model": None,
            "source": None,
            "legacy_list": True,
        }
    if isinstance(raw, dict):
        chunks = raw.get("chunks")
        if not isinstance(chunks, list):
            raise RuntimeError("The clinical embeddings index is missing a 'chunks' list.")
        return chunks, {
            "index_format_version": raw.get("index_format_version"),
            "embedding_model": raw.get("embedding_model"),
            "source": raw.get("source"),
            "legacy_list": False,
        }
    raise RuntimeError("The clinical embeddings index must be a JSON list or an object with 'chunks'.")


def _assert_embedding_model_compatible(metadata: dict[str, Any]) -> None:
    index_model = metadata.get("embedding_model")
    if not index_model:
        return
    configured = settings.embedding_model_name
    if index_model != configured:
        raise RuntimeError(
            "The clinical embeddings index was built with a different embedding "
            f"model ({index_model}) than the one configured ({configured}). "
            "Rebuild the index with python -m app.data.build_embeddings."
        )


def load_chunks() -> list[dict]:
    """Load clinical chunks and their stored embeddings with in-memory caching."""
    global _cached_chunks, _cached_file, _cached_mtime

    if not EMBEDDINGS_FILE.exists():
        _cached_chunks = None
        _cached_file = None
        _cached_mtime = None
        raise FileNotFoundError(
            "Clinical embeddings not found. Run "
            "'python -m app.data.build_embeddings' first."
        )

    current_mtime = EMBEDDINGS_FILE.stat().st_mtime
    if (
        _cached_chunks is not None
        and _cached_file == EMBEDDINGS_FILE
        and _cached_mtime == current_mtime
    ):
        return _cached_chunks

    try:
        raw = json.loads(EMBEDDINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("The clinical embeddings index is unreadable.") from exc

    chunks, metadata = parse_embeddings_payload(raw)
    _assert_embedding_model_compatible(metadata)
    _cached_chunks = chunks
    _cached_file = EMBEDDINGS_FILE
    _cached_mtime = current_mtime
    return _cached_chunks


SYMPTOM_TOPIC_TERMS = {
    "Breathing difficulty": (
        "breathing difficulty",
        "difficulty breathing",
        "breathing problems",
        "shortness of breath",
        "cough or difficulty",
        "cough and/or breathing",
        "cough",
    ),
    "Wheeze/tight chest": (
        "wheez",
        "tight chest",
    ),
    "Fever": ("fever", "febrile", "temperature"),
    "Chest pain": ("chest pain",),
    "Convulsions": ("convulsion", "seizure"),
    "Dizziness": ("dizziness", "vertigo"),
    "Headache": ("headache",),
    "Abdominal pain": ("abdominal pain", "abdominal symptom"),
    "Diarrhoea": ("diarrhoea", "diarrhea"),
}

URGENCY_QUERY_TERMS = (
    "danger sign",
    "danger signs",
    "emergency",
    "urgent",
    "urgently",
)

SYMPTOM_URGENT_HEADINGS = (
    "give urgent attention to the patient with",
    "give urgent attention to the child with",
    "give urgent attention to the patient who",
    "give urgent attention to the child who",
)


def infer_population_hint(query_lower: str) -> str | None:
    """Return Adult/Child only when the query unambiguously names that population."""
    has_child = "child" in query_lower or "children" in query_lower
    has_adult = "adult" in query_lower
    if has_child and not has_adult:
        return "Child"
    if has_adult and not has_child:
        return "Adult"
    return None


def infer_relevant_topics(query_lower: str) -> set[str]:
    """Map query phrases onto guideline symptom topics, not evaluation case IDs."""
    return {
        topic
        for topic, terms in SYMPTOM_TOPIC_TERMS.items()
        if any(term in query_lower for term in terms)
    }


def query_asks_about_urgency(query_lower: str) -> bool:
    return any(term in query_lower for term in URGENCY_QUERY_TERMS)


def has_symptom_urgent_heading(content_lower: str) -> bool:
    return any(heading in content_lower for heading in SYMPTOM_URGENT_HEADINGS)


def ranking_adjustments(
    chunk: dict,
    query_lower: str,
    relevant_topics: set[str],
    population_hint: str | None,
) -> float:
    """Light, source-grounded ranking adjustments on top of semantic similarity.

    Symptom-specific queries boost matching symptom topics. General emergency
    queries (no recognized symptom topic) prefer the Emergency patient chapter
    rather than every 'give urgent attention' heading, including injury pages.
    """
    adjustment = 0.0
    topic = chunk.get("topic")

    if topic in relevant_topics:
        adjustment += 0.08

    if population_hint is not None:
        population = chunk.get("population")
        if population == population_hint:
            adjustment += 0.12
        elif population in ("Adult", "Child"):
            adjustment -= 0.12

    if query_asks_about_urgency(query_lower):
        content_lower = chunk.get("content", "").lower()
        if relevant_topics:
            if topic in relevant_topics and has_symptom_urgent_heading(content_lower):
                adjustment += 0.12
        elif topic == "Emergency patient":
            adjustment += 0.12

    return adjustment


def search_clinical_guidelines(
    query: str,
    top_k: int = 3,
    min_semantic_score: float | None = None,
) -> list[dict]:
    """Rank guideline chunks using semantic similarity and light topic matching."""
    if not query.strip():
        raise ValueError("The search query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    threshold = (
        settings.min_semantic_score if min_semantic_score is None else min_semantic_score
    )

    chunks = load_chunks()
    query_lower = query.lower()
    population_hint = infer_population_hint(query_lower)
    relevant_topics = infer_relevant_topics(query_lower)

    query_embedding = get_model().encode(
        query,
        normalize_embeddings=True,
    )

    results = []

    for chunk in chunks:
        chunk_embedding = np.asarray(
            chunk["embedding"],
            dtype=np.float32,
        )

        norm = np.linalg.norm(chunk_embedding)
        if norm == 0:
            continue

        chunk_embedding = chunk_embedding / norm
        semantic_score = float(np.dot(query_embedding, chunk_embedding))
        ranking_score = semantic_score + ranking_adjustments(
            chunk,
            query_lower,
            relevant_topics,
            population_hint,
        )

        results.append({
            "id": chunk["id"],
            "topic": chunk["topic"],
            "population": chunk["population"],
            "page": chunk["page"],
            "source": chunk["source"],
            "content": chunk["content"],
            "score": semantic_score,
            "ranking_score": ranking_score,
        })

    results.sort(
        key=lambda item: item["ranking_score"],
        reverse=True,
    )

    above_threshold = [
        item for item in results if item["score"] >= threshold
    ]
    return above_threshold[:top_k]
