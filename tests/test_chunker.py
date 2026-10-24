import pytest

from app.data.chunker import create_chunks, detect_page_marker, detect_topic

URGENT_HEADING = (
    "Give urgent attention to the child with a fever "
    "(temperature ≥ 38°C now or in the past 3 days)"
)


def wrap_guideline(*sections: str) -> str:
    """Attach the required urgent child-fever section so create_chunks can run."""
    return "\n".join(
        [
            *sections,
            "Child 135",
            "Fever",
            "Routine fever guidance before the urgent section.",
            URGENT_HEADING,
            "Urgent action line one.",
            "Urgent action line two.",
            "Child 136",
            "Fever",
            "Follow-up guidance on the next page.",
        ]
    )


def test_page_markers_and_topic_aliases():
    assert detect_page_marker("adult 17") == ("Adult", 17)
    assert detect_page_marker("Child    128") == ("Child", 128)
    assert detect_topic("Cough or difficulty breathing") == "Breathing difficulty"


def test_detect_topic_recognizes_unnumbered_and_numbered_headings():
    assert detect_topic("Cough") == "Cough"
    assert detect_topic("Cough 141") == "Cough"
    assert detect_topic("Cough, recurrent 143") == "Cough"
    assert detect_topic("Wheeze") == "Wheeze/tight chest"
    assert detect_topic("Wheeze 142") == "Wheeze/tight chest"
    assert detect_topic("Wheeze/tight chest") == "Wheeze/tight chest"
    assert detect_topic("The emergency child") == "Emergency patient"
    assert detect_topic("Emergency child 128") == "Emergency patient"
    assert detect_topic("The emergency patient:") == "Emergency patient"
    assert detect_topic("Cough and/or breathing problems") == "Breathing difficulty"


def test_detect_topic_does_not_mislabel_unknown_or_injured_headings():
    assert detect_topic("Injured child 133") == "Injured child"
    assert detect_topic("Injured child 133") != "Emergency patient"
    assert detect_topic("The injured child") == "Injured child"
    assert detect_topic("An unrelated sentence") is None
    assert detect_topic("") is None
    assert detect_topic("Respiratory rate > 30") is None


def test_page_markers_are_not_treated_as_topics():
    assert detect_page_marker("Emergency child 128") == (None, None)
    assert detect_topic("Child 128") is None
    assert detect_page_marker("Child 128") == ("Child", 128)


def test_urgent_child_fever_section_is_kept_together():
    text = wrap_guideline()
    chunks = create_chunks(text, chunk_size=80)
    urgent = [chunk for chunk in chunks if chunk["content"].startswith(URGENT_HEADING)]

    assert len(urgent) == 1
    assert urgent[0]["population"] == "Child"
    assert urgent[0]["page"] == 135
    assert urgent[0]["topic"] == "Fever"
    assert "Urgent action line two." in urgent[0]["content"]
    assert "Child 136" not in urgent[0]["content"]
    assert all(chunk["content"].strip() for chunk in chunks)


def test_adult_and_child_section_boundaries_do_not_share_topics():
    text = wrap_guideline(
        "Adult 12",
        "The emergency patient",
        "Adult emergency danger signs.",
        "Child 128",
        "The emergency child",
        "Child emergency danger signs.",
    )
    chunks = create_chunks(text, chunk_size=200)
    adult = next(chunk for chunk in chunks if "Adult emergency danger signs." in chunk["content"])
    child = next(chunk for chunk in chunks if "Child emergency danger signs." in chunk["content"])

    assert adult["population"] == "Adult"
    assert adult["page"] == 12
    assert adult["topic"] == "Emergency patient"
    assert child["population"] == "Child"
    assert child["page"] == 128
    assert child["topic"] == "Emergency patient"


def test_topic_persists_across_page_markers_until_a_new_heading():
    text = wrap_guideline(
        "Child 128",
        "The emergency child",
        "Initial emergency assessment.",
        "Child 129",
        "Cardio-pulmonary resuscitation (CPR) of the child",
        "Continue emergency airway support.",
        "Child 131",
        "Seizures/convulsions",
        "Convulsion management.",
    )
    chunks = create_chunks(text, chunk_size=400)
    cpr = next(chunk for chunk in chunks if "Continue emergency airway support." in chunk["content"])
    seizures = next(chunk for chunk in chunks if "Convulsion management." in chunk["content"])

    assert cpr["population"] == "Child"
    assert cpr["page"] == 129
    assert cpr["topic"] == "Emergency patient"
    assert seizures["topic"] == "Convulsions"
    assert seizures["page"] == 131


def test_topic_transitions_from_breathing_difficulty_to_wheeze():
    text = wrap_guideline(
        "Child 141",
        "Cough and/or breathing problems",
        "Child cough and breathing assessment.",
        "Child 142",
        "Wheeze",
        "Give urgent attention to the child with wheeze and any of:",
        "Child 143",
        "Recurrent wheeze or cough",
        "Recurrent wheeze follow-up.",
    )
    chunks = create_chunks(text, chunk_size=400)
    breathing = next(
        chunk for chunk in chunks if "Child cough and breathing assessment." in chunk["content"]
    )
    wheeze = next(chunk for chunk in chunks if "child with wheeze" in chunk["content"])
    recurrent = next(chunk for chunk in chunks if "Recurrent wheeze follow-up." in chunk["content"])

    assert breathing["topic"] == "Breathing difficulty"
    assert breathing["page"] == 141
    assert wheeze["topic"] == "Wheeze/tight chest"
    assert wheeze["page"] == 142
    assert recurrent["topic"] == "Wheeze/tight chest"
    assert recurrent["page"] == 143


def test_adult_cough_or_difficulty_breathing_maps_to_breathing_difficulty():
    text = wrap_guideline(
        "Adult 29",
        "Cough or difficulty breathing",
        "Adult cough or difficulty breathing assessment.",
    )
    chunks = create_chunks(text, chunk_size=400)
    adult = next(
        chunk
        for chunk in chunks
        if "Adult cough or difficulty breathing assessment." in chunk["content"]
    )
    assert adult["population"] == "Adult"
    assert adult["page"] == 29
    assert adult["topic"] == "Breathing difficulty"
    assert adult["source"].startswith("Ethiopian Primary")


def test_injured_child_is_not_labeled_as_emergency_patient():
    text = wrap_guideline(
        "Child 133",
        "The injured child",
        "Give urgent attention to the injured child with any of:",
    )
    chunks = create_chunks(text, chunk_size=400)
    injured = next(chunk for chunk in chunks if "injured child with any of" in chunk["content"])
    assert injured["topic"] == "Injured child"
    assert injured["topic"] != "Emergency patient"
    assert injured["page"] == 133


def test_unknown_heading_does_not_invent_a_topic():
    text = wrap_guideline(
        "Adult 50",
        "An unrecognized clinical heading",
        "Body text under an unknown heading.",
    )
    chunks = create_chunks(text, chunk_size=400)
    unknown = next(
        chunk for chunk in chunks if "Body text under an unknown heading." in chunk["content"]
    )
    assert unknown["topic"] is None
    assert unknown["population"] == "Adult"
    assert unknown["page"] == 50


def test_missing_metadata_is_preserved_as_none_before_first_marker():
    text = wrap_guideline("Preface text with no page marker.")
    chunks = create_chunks(text, chunk_size=400)
    preface = next(chunk for chunk in chunks if "Preface text" in chunk["content"])
    assert preface["population"] is None
    assert preface["page"] is None
    assert preface["topic"] is None


def test_source_and_page_are_preserved_on_oversized_lines():
    long_line = "A" * 200
    text = wrap_guideline("Adult 22", "Headache", long_line)
    chunks = create_chunks(text, chunk_size=50)
    oversized = next(chunk for chunk in chunks if chunk["content"] == long_line)
    assert oversized["page"] == 22
    assert oversized["population"] == "Adult"
    assert oversized["topic"] == "Headache"
    assert oversized["source"]


def test_chunker_rejects_missing_required_urgent_section():
    with pytest.raises(ValueError, match="urgent child-fever section"):
        create_chunks("Adult 1\nFever\nA short passage.")


def test_chunker_rejects_empty_or_malformed_inputs():
    with pytest.raises(ValueError, match="urgent child-fever section"):
        create_chunks("")
    with pytest.raises(ValueError, match="urgent child-fever section"):
        create_chunks("   \n\n")


def test_chunker_rejects_invalid_chunk_size():
    with pytest.raises(ValueError, match="chunk_size"):
        create_chunks("text", chunk_size=0)
