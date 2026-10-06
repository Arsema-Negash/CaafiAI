from pathlib import Path


PROCESSED_DATA_DIR = Path("data/processed")


def create_chunks(text: str, chunk_size: int = 1500) -> list[str]:
    """
    Split processed clinical text into manageable chunks.

    The first version keeps chunks reasonably small while
    preserving paragraph boundaries.
    """

    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n")
        if paragraph.strip()
    ]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
            current_chunk += paragraph + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())

            current_chunk = paragraph + "\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def load_processed_document() -> str:
    """Load the processed clinical guideline."""

    files = list(PROCESSED_DATA_DIR.glob("*.txt"))

    if not files:
        raise FileNotFoundError(
            "No processed text document found in data/processed."
        )

    return files[0].read_text(encoding="utf-8")


if __name__ == "__main__":
    text = load_processed_document()
    chunks = create_chunks(text)

    print(f"Total chunks created: {len(chunks)}")

    for i, chunk in enumerate(chunks[:3], start=1):
        print(f"\n--- Chunk {i} ---")
        print(chunk[:500])