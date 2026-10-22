"""Unit tests for PDF text cleanup (no filesystem/network side effects)."""
from app.data.ingestion import clean_text


def test_clean_text_repairs_common_encoding_artifacts():
    assert clean_text("Itâ€™s â€œimportantâ€ Â test") == "It’s “important”  test"


def test_clean_text_trims_and_removes_blank_lines():
    assert clean_text("  first line  \n\n   second line \n") == "first line\nsecond line"
