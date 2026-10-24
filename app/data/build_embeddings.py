from pathlib import Path
import json

from app.data.chunker import load_processed_document, create_chunks
from app.ai.embeddings import get_model


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "embeddings"
OUTPUT_FILE = EMBEDDINGS_DIR / "clinical_chunks.json"


def build_embeddings():
    """Create embeddings for all clinical guideline chunks."""

    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

    text = load_processed_document()
    chunks = create_chunks(text)

    print(f"Creating embeddings for {len(chunks)} chunks...")

    model = get_model()
    contents = [chunk["content"] for chunk in chunks]
    embeddings = model.encode(
        contents,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist()

    OUTPUT_FILE.write_text(
        json.dumps(chunks, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved embeddings to: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_embeddings()