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
