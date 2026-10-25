"""Application configuration and environment settings for CAAFI_AI."""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings:
    """Runtime configuration settings loaded from environment variables."""

    def __init__(self) -> None:
        self.project_name: str = os.getenv("PROJECT_NAME", "CAAFI_AI")
        self.version: str = "0.1.0"
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

        # Paths
        default_embeddings = PROJECT_ROOT / "data" / "embeddings" / "clinical_chunks.json"
        self.embeddings_path: Path = Path(os.getenv("EMBEDDINGS_FILE", str(default_embeddings)))
        self.raw_data_dir: Path = Path(os.getenv("RAW_DATA_DIR", str(PROJECT_ROOT / "data" / "raw")))
        self.processed_data_dir: Path = Path(
            os.getenv("PROCESSED_DATA_DIR", str(PROJECT_ROOT / "data" / "processed"))
        )

        # Retrieval & Safety Limits
        self.default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "3"))
        self.max_top_k: int = int(os.getenv("MAX_TOP_K", "10"))
        self.max_message_length: int = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))
        # Floor for semantic cosine similarity. Historical core-eval rank-1 scores
        # were at least ~0.37; 0.25 is an engineering abstention floor, not a
        # clinical relevance threshold.
        self.min_semantic_score: float = float(os.getenv("MIN_SEMANTIC_SCORE", "0.25"))

        # Embedding model (local sentence-transformers). Must match the index.
        self.embedding_model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        self.index_format_version: int = int(os.getenv("INDEX_FORMAT_VERSION", "1"))
        self.guideline_source_name: str = os.getenv(
            "GUIDELINE_SOURCE_NAME",
            "Ethiopian Primary Health Care Clinical Guidelines, 2017",
        )


settings = Settings()
