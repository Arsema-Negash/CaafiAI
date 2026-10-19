from pathlib import Path
import json

from app.data.chunker import load_processed_document, create_chunks
from app.ai.embeddings import model


EMBEDDINGS_DIR = Path("data/embeddings")
OUTPUT_FILE = EMBEDDINGS_DIR / "clinical_chunks.json"


def build_embeddings():
    """Create embeddings for all clinical guideline chunks."""

    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

    text = load_processed_document()
    chunks = create_chunks(text)

    print(f"Creating embeddings for {len(chunks)} chunks...")

    for i, chunk in enumerate(chunks, start=1):
        chunk["embedding"] = model.encode(
            chunk["content"]
        ).tolist()

        if i % 25 == 0:
            print(f"Processed {i}/{len(chunks)} chunks")

    OUTPUT_FILE.write_text(
        json.dumps(chunks, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved embeddings to: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_embeddings()