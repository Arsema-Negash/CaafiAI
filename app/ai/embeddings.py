"""Embedding model loading, kept lazy so health endpoints can start independently."""
from functools import lru_cache

MODEL_NAME = "all-MiniLM-L6-v2"


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

    return SentenceTransformer(MODEL_NAME)


def create_embedding(text: str):
    """Convert text into a normalized numerical embedding."""
    if not text or not text.strip():
        raise ValueError("Text to embed cannot be empty.")
    return get_model().encode(text, normalize_embeddings=True)
