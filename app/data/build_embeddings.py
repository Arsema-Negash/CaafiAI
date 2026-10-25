"""Build local clinical guideline embeddings from processed chunks."""
from pathlib import Path
import json

from app.data.chunker import load_processed_document, create_chunks
from app.ai.embeddings import get_model
from app.core.config import settings


def build_embeddings() -> None:
    """Create embeddings for all clinical guideline chunks and write the index."""
    output_file = settings.embeddings_path
    output_file.parent.mkdir(parents=True, exist_ok=True)

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

    payload = {
        "index_format_version": settings.index_format_version,
        "embedding_model": settings.embedding_model_name,
        "source": settings.guideline_source_name,
        "chunk_count": len(chunks),
        "chunks": chunks,
    }
    output_file.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved embeddings to: {output_file}")


if __name__ == "__main__":
    build_embeddings()
