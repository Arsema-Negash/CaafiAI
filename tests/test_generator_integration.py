"""Unit tests for grounded generation contracts; Gemini itself is mocked."""
import sys
from types import SimpleNamespace

import pytest

from app.ai import generator
from app.core.config import settings

SOURCES = [{
    "topic": "Fever", "population": "Adult", "page": 88,
    "source": "Ethiopian Primary Health Care Clinical Guidelines, 2017",
    "content": "The guideline says to assess fever according to the clinical assessment section.",
}]


def test_prompt_includes_only_returned_evidence_and_requested_language():
    prompt = generator._build_prompt("What about this?", SOURCES, "am", [
        {"role": "user", "content": "I have fever"},
        {"role": "assistant", "content": "Previous answer"},
    ])
    assert "The guideline says to assess fever" in prompt
    assert "page 88" in prompt
    assert "Amharic (አማርኛ)" in prompt
    assert "I have fever" in prompt
    assert "only source of medical facts" in prompt.lower()


def test_grounded_generator_passes_evidence_to_gemini_and_returns_model(monkeypatch):
    captured = {}

    class FakeModel:
        def __init__(self, **kwargs):
            captured["system_instruction"] = kwargs["system_instruction"]

        def generate_content(self, prompt):
            captured["prompt"] = prompt
            return SimpleNamespace(text="The provided excerpt discusses fever assessment. Please review with a qualified health professional.")

    fake_genai = SimpleNamespace(
        configure=lambda **kwargs: captured.update(api_key=kwargs["api_key"]),
        GenerativeModel=FakeModel,
        GenerationConfig=lambda **kwargs: kwargs,
    )
    fake_google = SimpleNamespace(generativeai=fake_genai)
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.generativeai", fake_genai)
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(settings, "enable_generative", True)

    result = generator.generate_grounded_response("What does the guideline say about fever?", SOURCES, "en")
    assert result["model"] == settings.gemini_model
    assert "The provided excerpt discusses fever assessment" in result["response"]
    assert "The guideline says to assess fever" in captured["prompt"]
    assert "test-key" == captured["api_key"]


def test_generation_refuses_to_run_without_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    with pytest.raises(generator.GenerationUnavailableError):
        generator.generate_grounded_response("fever", SOURCES)


def test_generic_background_is_demoted_for_symptom_queries():
    from app.ai.retrieval import ranking_adjustments
    background = {"topic": "Fever", "content": "The majority of the population lives in rural areas."}
    clinical = {"topic": "Fever", "content": "Assess the patient with fever and danger signs."}
    background_adjustment = ranking_adjustments(background, "fever", {"Fever"}, None)
    clinical_adjustment = ranking_adjustments(clinical, "fever", {"Fever"}, None)
    assert background_adjustment < clinical_adjustment


def test_generic_background_detector_does_not_flag_clinical_guidance():
    from app.ai.retrieval import is_generic_background_passage
    assert is_generic_background_passage("The health system in Ethiopia is organized by region.")
    assert not is_generic_background_passage("Give urgent attention to the patient with fever and confusion.")


def test_table_of_contents_passages_are_not_returned_as_evidence(tmp_path, monkeypatch):
    import json
    import numpy as np
    from app.ai import retrieval

    index = tmp_path / "chunks.json"
    index.write_text(json.dumps([
        {"id": 1, "topic": "Fever", "population": None, "page": None,
         "source": "Test guideline", "content": "wheeze 30 wound 14 adult contents: fever 17",
         "embedding": [1.0, 0.0]},
        {"id": 2, "topic": "Fever", "population": "Adult", "page": 17,
         "source": "Test guideline", "content": "Give clinical assessment to the patient with fever.",
         "embedding": [1.0, 0.0]},
    ]), encoding="utf-8")
    monkeypatch.setattr(retrieval, "EMBEDDINGS_FILE", index)
    monkeypatch.setattr(retrieval, "get_model", lambda: SimpleNamespace(encode=lambda *a, **k: np.array([1.0, 0.0])))
    results = retrieval.search_clinical_guidelines("fever in an adult", top_k=1)
    assert results
    assert results[0]["id"] == 2
    assert results[0]["page"] == 17


def test_basic_grounding_guard_rejects_page_not_in_sources():
    assert not generator.generated_response_passes_basic_grounding_checks(
        "See page 999 for the recommendation.", SOURCES
    )


def test_basic_grounding_guard_rejects_unsupported_dose():
    assert not generator.generated_response_passes_basic_grounding_checks(
        "Take 500 mg every day. Please review with a qualified health professional.", SOURCES
    )


def test_basic_grounding_guard_allows_answer_without_unverified_dose_or_page():
    assert generator.generated_response_passes_basic_grounding_checks(
        "The retrieved excerpt describes assessment of fever. Please review with a qualified health professional.", SOURCES
    )
