"""Embedding model loading, kept lazy so health endpoints can start independently."""
from functools import lru_cache

from app.core.config import settings

MODEL_NAME = settings.embedding_model_name


@lru_cache(maxsize=1)
def get_model():
    """Load the sentence-transformer once, when embeddings are actually needed."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "The sentence-transformers package is missing. "
            "Install the project requirements before using clinical retrieval."
        ) from exc

    model_name = settings.embedding_model_name
    # Prefer local cached weights to avoid outbound network latency or timeouts.
    try:
        return SentenceTransformer(model_name, local_files_only=True)
    except Exception:
        return SentenceTransformer(model_name)


def create_embedding(text: str):
    """Convert text into a normalized numerical embedding."""
    if not text or not text.strip():
        raise ValueError("Text to embed cannot be empty.")
    return get_model().encode(text, normalize_embeddings=True)
