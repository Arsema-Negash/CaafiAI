from pathlib import Path
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from every page of a PDF."""

    reader = PdfReader(pdf_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages)


def clean_text(text: str) -> str:
    """Clean common PDF extraction artifacts."""

    replacements = {
        "â€™": "’",
        "â€˜": "‘",
        "â€œ": "“",
        "â€": "”",
        "â€“": "–",
        "â€”": "—",
        "â€¢": "•",
        "Â": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    lines = []

    for line in text.splitlines():
        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


def save_processed_text(text: str, filename: str) -> Path:
    """Save processed document text."""

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_path = PROCESSED_DATA_DIR / filename

    output_path.write_text(
        text,
        encoding="utf-8"
    )

    return output_path


def process_pdf(pdf_path: Path) -> Path:
    """Extract, clean, and save a PDF as text."""

    raw_text = extract_text_from_pdf(pdf_path)

    cleaned_text = clean_text(raw_text)

    output_filename = f"{pdf_path.stem}.txt"

    return save_processed_text(
        cleaned_text,
        output_filename
    )

if __name__ == "__main__":
    pdf_files = sorted(RAW_DATA_DIR.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in {RAW_DATA_DIR}. Copy the authorized clinical guideline PDF there first."
        )
    for pdf_file in pdf_files:
        output_file = process_pdf(pdf_file)
        print(f"Processed {pdf_file.name} -> {output_file}")
