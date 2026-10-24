from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

SOURCE_NAME = "Ethiopian Primary Health Care Clinical Guidelines, 2017"

TOPIC_ALIASES = {
    "emergency patient": "Emergency patient",
    "the emergency patient": "Emergency patient",
    "emergency child": "Emergency patient",
    "the emergency child": "Emergency patient",
    "unconscious patient": "Unconscious patient",
    "the unconscious patient": "Unconscious patient",
    "decreased level of consciousness": "Decreased level of consciousness",
    "injured patient": "Injured patient",
    "the injured patient": "Injured patient",
    "injured child": "Injured child",
    "the injured child": "Injured child",
    "convulsions": "Convulsions",
    "seizures/convulsions": "Convulsions",
    "dizziness/vertigo": "Dizziness",
    "dizziness": "Dizziness",
    "headache": "Headache",
    "fever": "Fever",
    "breathing difficulty": "Breathing difficulty",
    "cough or difficulty breathing": "Breathing difficulty",
    "cough and/or breathing problems": "Breathing difficulty",
    "cough": "Cough",
    "cough, recurrent": "Cough",
    "wheeze": "Wheeze/tight chest",
    "wheeze/tight chest": "Wheeze/tight chest",
    "wheeze, recurrent": "Wheeze/tight chest",
    "recurrent wheeze or cough": "Wheeze/tight chest",
    "chest pain": "Chest pain",
    "abdominal pain": "Abdominal pain",
    "abdominal symptoms": "Abdominal pain",
    "diarrhoea": "Diarrhoea",
    "breast symptoms": "Breast symptoms",
}


def load_processed_document() -> str:
    files = sorted(PROCESSED_DATA_DIR.glob("*.txt"))
    files = [file for file in files if file.name != "chunks.txt"]

    if not files:
        raise FileNotFoundError("No processed clinical guideline found.")

    return files[0].read_text(encoding="utf-8")


def detect_page_marker(line: str):
    match = re.fullmatch(
        r"(Adult|Child)\s+(\d+)",
        line.strip(),
        re.IGNORECASE,
    )

    if match:
        return match.group(1).capitalize(), int(match.group(2))

    return None, None


def _normalize_heading(line: str) -> str:
    return line.strip().lower().rstrip(":.").strip()


def detect_topic(line: str):
    normalized = _normalize_heading(line)

    # Preserve exact matches for existing topic headings.
    topic = TOPIC_ALIASES.get(normalized)
    if topic:
        return topic

    # Recognize headings that end with a page number, e.g. "Cough 141".
    numbered_heading = re.fullmatch(r"(.+?)\s+\d+", normalized)
    if numbered_heading:
        heading = numbered_heading.group(1).strip()
        return TOPIC_ALIASES.get(heading)

    return None


def extract_urgent_child_fever_section(lines: list[str]) -> str | None:
    """Extract the urgent child-fever section and its management."""
    start_text = (
        "Give urgent attention to the child with a fever "
        "(temperature ≥ 38°C now or in the past 3 days)"
    )

    start = next(
        (i for i, line in enumerate(lines) if line.startswith(start_text)),
        None,
    )

    if start is None:
        return None

    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if re.fullmatch(r"Child\s+136", lines[i], re.IGNORECASE)
        ),
        None,
    )

    if end is None:
        return None

    return "\n".join(lines[start:end]).strip()


def create_chunks(text: str, chunk_size: int = 1500) -> list[dict]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1.")

    chunks = []
    current_lines = []
    current_length = 0
    population = None
    page = None
    topic = None

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    urgent_child_fever = extract_urgent_child_fever_section(lines)

    if urgent_child_fever is None:
        raise ValueError(
            "Could not locate the complete urgent child-fever section."
        )

    urgent_start = next(
        i
        for i, line in enumerate(lines)
        if line.startswith(
            "Give urgent attention to the child with a fever "
            "(temperature ≥ 38°C now or in the past 3 days)"
        )
    )

    urgent_end = urgent_start + len(urgent_child_fever.splitlines())

    def save_chunk():
        nonlocal current_lines, current_length

        if current_lines:
            chunks.append(
                {
                    "id": len(chunks) + 1,
                    "population": population,
                    "page": page,
                    "topic": topic,
                    "content": "\n".join(current_lines),
                    "source": SOURCE_NAME,
                }
            )

        current_lines = []
        current_length = 0

    i = 0

    while i < len(lines):
        if i == urgent_start:
            save_chunk()

            chunks.append(
                {
                    "id": len(chunks) + 1,
                    "population": "Child",
                    "page": 135,
                    "topic": "Fever",
                    "content": urgent_child_fever,
                    "source": SOURCE_NAME,
                }
            )

            i = urgent_end
            continue

        line = lines[i]

        detected_population, detected_page = detect_page_marker(line)

        if detected_population:
            save_chunk()
            # A page number is not a topic change. Keep the current topic
            # until a new heading appears, but reset when Adult/Child changes.
            if detected_population != population:
                topic = None
            population = detected_population
            page = detected_page
            i += 1
            continue

        detected_topic = detect_topic(line)

        if detected_topic:
            save_chunk()
            topic = detected_topic

        if len(line) > chunk_size:
            save_chunk()
            chunks.append(
                {
                    "id": len(chunks) + 1,
                    "population": population,
                    "page": page,
                    "topic": topic,
                    "content": line,
                    "source": SOURCE_NAME,
                }
            )
            i += 1
            continue

        additional_length = len(line) + (1 if current_lines else 0)

        if current_length + additional_length > chunk_size:
            save_chunk()

        current_lines.append(line)
        current_length += additional_length
        i += 1

    save_chunk()
    return chunks


if __name__ == "__main__":
    text = load_processed_document()
    chunks = create_chunks(text)

    print(f"Total chunks created: {len(chunks)}")
    print(
        "Chunks without content: "
        f"{sum(not c['content'].strip() for c in chunks)}"
    )
    print(
        "Chunks over 1500 characters: "
        f"{sum(len(c['content']) > 1500 for c in chunks)}"
    )

    for chunk in chunks[:5]:
        print("\n--------------------")
        print(f"ID: {chunk['id']}")
        print(f"Population: {chunk['population']}")
        print(f"Page: {chunk['page']}")
        print(f"Topic: {chunk['topic']}")
        print(f"Content:\n{chunk['content'][:300]}")
