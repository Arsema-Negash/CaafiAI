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

    # Infer population only when the question explicitly identifies it.
    population_hint = None
    if "child" in query_lower or "children" in query_lower:
        population_hint = "Child"
    elif "adult" in query_lower:
        population_hint = "Adult"

    topic_terms = {
        "Breathing difficulty": (
            "breathing difficulty",
            "difficulty breathing",
            "breathing problems",
            "cough",
            "shortness of breath",
        ),
        "Wheeze/tight chest": (
            "wheez",
            "tight chest",
        ),
        "Fever": ("fever", "febrile", "temperature"),
        "Chest pain": ("chest pain",),
        "Convulsions": ("convulsion", "seizure"),
    }

    relevant_topics = {
        topic
        for topic, terms in topic_terms.items()
        if any(term in query_lower for term in terms)
    }

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

        # Keep semantic similarity as the primary ranking signal.
        ranking_score = semantic_score

        content_lower = chunk.get("content", "").lower()

        # Prefer source chunks explicitly labeled for urgent attention
        # when the user asks about danger signs or emergencies.
        asks_about_urgency = any(
            term in query_lower
            for term in (
                "danger sign",
                "danger signs",
                "emergency",
                "urgent",
                "urgently",
            )
        )

        has_urgent_heading = (
            "give urgent attention to the patient" in content_lower
            or "give urgent attention to the child" in content_lower
        )

        if asks_about_urgency and has_urgent_heading:
            ranking_score += 0.12

        if chunk.get("topic") in relevant_topics:
            ranking_score += 0.08

        if population_hint is not None:
            if chunk.get("population") == population_hint:
                ranking_score += 0.12
            elif chunk.get("population") in ("Adult", "Child"):
                ranking_score -= 0.12

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
