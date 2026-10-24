import json

import numpy as np
import pytest

from app.ai import retrieval


class FakeModel:
    def encode(self, text, normalize_embeddings=True):
        assert normalize_embeddings is True
        return np.array([1.0, 0.0], dtype=np.float32)


def test_retrieval_ranks_relevant_population_and_topic(tmp_path, monkeypatch):
    data = [
        {
            "id": 1, "topic": "Fever", "population": "Child", "page": 135,
            "source": "Test guideline", "content": "Child fever guidance",
            "embedding": [1.0, 0.0],
        },
        {
            "id": 2, "topic": "Breathing difficulty", "population": "Adult", "page": 29,
            "source": "Test guideline", "content": "Adult breathing guidance",
            "embedding": [0.0, 1.0],
        },
    ]
    index = tmp_path / "chunks.json"
    index.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(retrieval, "EMBEDDINGS_FILE", index)
    monkeypatch.setattr(retrieval, "get_model", lambda: FakeModel())

    results = retrieval.search_clinical_guidelines("fever in a child", top_k=2)

    assert results[0]["id"] == 1
    assert results[0]["population"] == "Child"
    assert results[0]["topic"] == "Fever"
    assert results[0]["score"] == pytest.approx(1.0)


def test_retrieval_rejects_blank_query():
    with pytest.raises(ValueError, match="empty"):
        retrieval.search_clinical_guidelines("  ")


def test_retrieval_rejects_nonpositive_top_k():
    with pytest.raises(ValueError, match="at least 1"):
        retrieval.search_clinical_guidelines("fever", top_k=0)


def _write_index(tmp_path, monkeypatch, rows):
    index = tmp_path / "chunks.json"
    index.write_text(json.dumps(rows), encoding="utf-8")
    monkeypatch.setattr(retrieval, "EMBEDDINGS_FILE", index)
    monkeypatch.setattr(retrieval, "get_model", lambda: FakeModel())


def test_general_emergency_query_prefers_emergency_topic_over_injured_child(
    tmp_path, monkeypatch
):
    _write_index(
        tmp_path,
        monkeypatch,
        [
            {
                "id": 1,
                "topic": "Injured child",
                "population": "Child",
                "page": 133,
                "source": "Test guideline",
                "content": "Give urgent attention to the injured child with any of:",
                "embedding": [0.41, 0.912],
            },
            {
                "id": 2,
                "topic": "Emergency patient",
                "population": "Child",
                "page": 128,
                "source": "Test guideline",
                "content": "Give urgent attention to the emergency child",
                "embedding": [0.40, 0.9165],
            },
        ],
    )

    results = retrieval.search_clinical_guidelines(
        "What are the general emergency danger signs for a child?",
        top_k=2,
    )

    assert results[0]["id"] == 2
    assert results[0]["topic"] == "Emergency patient"


def test_wheeze_query_prefers_wheeze_over_breathing_difficulty(tmp_path, monkeypatch):
    _write_index(
        tmp_path,
        monkeypatch,
        [
            {
                "id": 1,
                "topic": "Breathing difficulty",
                "population": "Child",
                "page": 141,
                "source": "Test guideline",
                "content": "Cough and/or breathing problems. If wheeze see next page.",
                "embedding": [0.52, 0.854],
            },
            {
                "id": 2,
                "topic": "Wheeze/tight chest",
                "population": "Child",
                "page": 142,
                "source": "Test guideline",
                "content": "Give urgent attention to the child with wheeze and any of:",
                "embedding": [0.50, 0.866],
            },
        ],
    )

    results = retrieval.search_clinical_guidelines(
        "What guidance is relevant when a child has wheezing or a tight chest?",
        top_k=2,
    )

    assert results[0]["topic"] == "Wheeze/tight chest"


def test_chunks_with_missing_metadata_can_still_rank_by_similarity(tmp_path, monkeypatch):
    _write_index(
        tmp_path,
        monkeypatch,
        [
            {
                "id": 1,
                "topic": None,
                "population": None,
                "page": None,
                "source": "Test guideline",
                "content": "Unlabeled preface",
                "embedding": [1.0, 0.0],
            },
            {
                "id": 2,
                "topic": "Fever",
                "population": "Child",
                "page": 135,
                "source": "Test guideline",
                "content": "Child fever",
                "embedding": [0.0, 1.0],
            },
        ],
    )

    results = retrieval.search_clinical_guidelines("unlabeled preface text", top_k=2)
    assert results[0]["id"] == 1
    assert results[0]["topic"] is None


def test_zero_norm_embeddings_are_skipped(tmp_path, monkeypatch):
    _write_index(
        tmp_path,
        monkeypatch,
        [
            {
                "id": 1,
                "topic": "Fever",
                "population": "Child",
                "page": 135,
                "source": "Test guideline",
                "content": "bad vector",
                "embedding": [0.0, 0.0],
            },
            {
                "id": 2,
                "topic": "Fever",
                "population": "Child",
                "page": 135,
                "source": "Test guideline",
                "content": "Child fever guidance",
                "embedding": [1.0, 0.0],
            },
        ],
    )

    results = retrieval.search_clinical_guidelines("fever in a child", top_k=5)
    assert [item["id"] for item in results] == [2]


def test_infer_population_hint_neutral_when_both_present():
    assert retrieval.infer_population_hint("fever in adults and children") is None
    assert retrieval.infer_population_hint("child fever") == "Child"
    assert retrieval.infer_population_hint("adult cough") == "Adult"
    assert retrieval.infer_population_hint("general headache") is None


def test_retrieval_reloads_when_embeddings_file_is_updated(tmp_path, monkeypatch):
    index1 = tmp_path / "chunks1.json"
    index1.write_text(
        json.dumps([
            {
                "id": 101,
                "topic": "Fever",
                "population": "Adult",
                "page": 20,
                "source": "Guide 1",
                "content": "Fever v1",
                "embedding": [1.0, 0.0],
            }
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(retrieval, "EMBEDDINGS_FILE", index1)
    monkeypatch.setattr(retrieval, "get_model", lambda: FakeModel())

    res1 = retrieval.search_clinical_guidelines("fever", top_k=1)
    assert res1[0]["id"] == 101

    # Now point to index2 with different chunk id
    index2 = tmp_path / "chunks2.json"
    index2.write_text(
        json.dumps([
            {
                "id": 202,
                "topic": "Fever",
                "population": "Adult",
                "page": 20,
                "source": "Guide 2",
                "content": "Fever v2",
                "embedding": [1.0, 0.0],
            }
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(retrieval, "EMBEDDINGS_FILE", index2)
    res2 = retrieval.search_clinical_guidelines("fever", top_k=1)
    assert res2[0]["id"] == 202

