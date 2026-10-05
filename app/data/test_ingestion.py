from pathlib import Path

from app.data.ingestion import process_pdf


pdf_path = Path(
    "data/raw/Ethiopian Primary care clinical guideline 2017 - DIGITAL final draft (4).pdf"
)

output_path = process_pdf(pdf_path)

print(f"Processed document saved to: {output_path}")