import json
from pathlib import Path

import numpy as np

from app.ai.embeddings import get_model

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMBEDDINGS_FILE = PROJECT_ROOT / "data" / "embeddings" / "clinical_chunks.json"


def load_chunks() -> list[dict]:
    """Load clinical chunks and their stored embeddings."""
    if not EMBEDDINGS_FILE.exists():
        raise FileNotFoundError(
            "Clinical embeddings not found. Run "
            "'python -m app.data.build_embeddings' first."
        )

    return json.loads(EMBEDDINGS_FILE.read_text(encoding="utf-8"))


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
    """Return Adult/Child only when the query names that population."""
    if "child" in query_lower or "children" in query_lower:
        return "Child"
    if "adult" in query_lower:
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
) -> list[dict]:
    """Rank guideline chunks using semantic similarity and light topic matching."""
    if not query.strip():
        raise ValueError("The search query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

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

    return results[:top_k]
