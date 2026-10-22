import pytest

from app.data.chunker import create_chunks, detect_page_marker, detect_topic

URGENT_HEADING = (
    "Give urgent attention to the child with a fever "
    "(temperature ≥ 38°C now or in the past 3 days)"
)


def test_page_markers_and_topic_aliases():
    assert detect_page_marker("adult 17") == ("Adult", 17)
    assert detect_topic("Cough or difficulty breathing") == "Breathing difficulty"


def test_urgent_child_fever_section_is_kept_together():
    text = "\n".join([
        "Child 135",
        "Fever",
        "Routine fever guidance before the urgent section.",
        URGENT_HEADING,
        "Urgent action line one.",
        "Urgent action line two.",
        "Child 136",
        "Fever",
        "Follow-up guidance on the next page.",
    ])

    chunks = create_chunks(text, chunk_size=80)
    urgent = [chunk for chunk in chunks if chunk["content"].startswith(URGENT_HEADING)]

    assert len(urgent) == 1
    assert urgent[0]["population"] == "Child"
    assert urgent[0]["page"] == 135
    assert urgent[0]["topic"] == "Fever"
    assert "Urgent action line two." in urgent[0]["content"]
    assert "Child 136" not in urgent[0]["content"]
    assert all(chunk["content"].strip() for chunk in chunks)


def test_chunker_rejects_missing_required_urgent_section():
    with pytest.raises(ValueError, match="urgent child-fever section"):
        create_chunks("Adult 1\nFever\nA short passage.")


def test_chunker_rejects_invalid_chunk_size():
    with pytest.raises(ValueError, match="chunk_size"):
        create_chunks("text", chunk_size=0)
