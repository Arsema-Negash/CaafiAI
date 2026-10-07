from pathlib import Path
import re


PROCESSED_DATA_DIR = Path("data/processed")


# Main clinical topics from the Ethiopian Primary Health Care Clinical Guidelines
TOPICS = [
    "Emergency patient",
    "Convulsions",
    "Dizziness",
    "Headache",
    "Fever",
    "Breathing difficulty",
    "Chest pain",
    "Cough",
    "Abdominal pain",
    "Diarrhoea",
]


def load_processed_document() -> str:
    """Load the processed clinical guideline."""

    files = list(PROCESSED_DATA_DIR.glob("*.txt"))

    # Ignore generated chunk files
    files = [file for file in files if file.name != "chunks.txt"]

    if not files:
        raise FileNotFoundError(
            "No processed clinical guideline found."
        )

    return files[0].read_text(encoding="utf-8")


def detect_page_marker(line: str):
    """
    Detect Adult/Child page markers such as:
    Adult 17
    Child 135
    """

    match = re.fullmatch(r"(Adult|Child)\s+(\d+)", line.strip())

    if match:
        return match.group(1), int(match.group(2))

    return None, None


def detect_topic(line: str):
    """Detect a known clinical topic heading."""

    cleaned = line.strip()

    for topic in TOPICS:
        if cleaned.lower() == topic.lower():
            return topic

    return None


def create_chunks(text: str, chunk_size: int = 1500) -> list[dict]:
    """
    Create chunks while keeping track of population, page, and topic.
    """

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    chunks = []

    current_lines = []
    current_length = 0

    population = None
    page = None
    topic = None

    for line in lines:

        detected_population, detected_page = detect_page_marker(line)

        if detected_population:
            population = detected_population
            page = detected_page
            continue

        detected_topic = detect_topic(line)

        if detected_topic:
            topic = detected_topic

        if current_length + len(line) <= chunk_size:
            current_lines.append(line)
            current_length += len(line)

        else:
            if current_lines:
                chunks.append(
                    {
                        "id": len(chunks) + 1,
                        "population": population,
                        "page": page,
                        "topic": topic,
                        "content": "\n".join(current_lines),
                        "source": (
                            "Ethiopian Primary Health Care "
                            "Clinical Guidelines, 2017"
                        ),
                    }
                )

            current_lines = [line]
            current_length = len(line)

    if current_lines:
        chunks.append(
            {
                "id": len(chunks) + 1,
                "population": population,
                "page": page,
                "topic": topic,
                "content": "\n".join(current_lines),
                "source": (
                    "Ethiopian Primary Health Care "
                    "Clinical Guidelines, 2017"
                ),
            }
        )

    return chunks


if __name__ == "__main__":
    text = load_processed_document()

    chunks = create_chunks(text)

    print(f"Total chunks created: {len(chunks)}")

    for chunk in chunks[:5]:
        print("\n--------------------")
        print(f"ID: {chunk['id']}")
        print(f"Population: {chunk['population']}")
        print(f"Page: {chunk['page']}")
        print(f"Topic: {chunk['topic']}")
        print(f"Source: {chunk['source']}")
        print(f"Content:\n{chunk['content'][:300]}")