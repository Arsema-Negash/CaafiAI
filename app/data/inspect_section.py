from pathlib import Path

file_path = Path(
    "data/processed/Ethiopian Primary care clinical guideline "
    "2017 - DIGITAL final draft (4).txt"
)

lines = file_path.read_text(encoding="utf-8").splitlines()

sections = [
    (1225, 1265),  # Fever section
    (2450, 2500),  # Possible breathing-related guidance
    (9240, 9350),  # Child fever section
]

for start, end in sections:
    print(f"\n{'=' * 20} Lines {start}-{end} {'=' * 20}")

    for line_number in range(start, min(end, len(lines)) + 1):
        print(f"{line_number}: {lines[line_number - 1]}")
