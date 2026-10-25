from app.core.ai_engine import EXCERPT_CHAR_LIMIT, compose_extractive_response, generate_health_response


def test_extractive_response_quotes_only_source_text():
    sources = [
        {
            "topic": "Fever",
            "population": "Child",
            "page": 135,
            "content": "Give urgent attention to the child with a fever.",
        }
    ]
    text = compose_extractive_response(sources)
    assert "not a diagnosis" in text
    assert "Give urgent attention to the child with a fever." in text
    assert "page 135" in text
    assert "prescribe" not in text.lower()


def test_extractive_response_empty_sources_states_limitation():
    text = compose_extractive_response([])
    assert "could not retrieve" in text
    assert "no risk exists" in text


def test_excerpt_is_a_prefix_of_the_source_chunk_only():
    content = "Give urgent attention to the child with a fever. " + ("Keep quoting only this source. " * 40)
    sources = [{"topic": "Fever", "population": "Child", "page": 135, "content": content}]
    text = compose_extractive_response(sources)
    quoted = text.split("] ", 1)[1]
    if quoted.endswith("…"):
        quoted = quoted[:-1]
    collapsed = " ".join(content.split())
    assert collapsed.startswith(quoted)
    assert len(quoted) <= EXCERPT_CHAR_LIMIT


def test_generate_health_response_insufficient_when_retrieval_empty(monkeypatch):
    from app.core import ai_engine

    monkeypatch.setattr(ai_engine, "search_clinical_guidelines", lambda query, top_k: [])
    result = generate_health_response("unrelated hobby question")
    assert result["evidence_status"] == "insufficient"
    assert result["sources"] == []
    assert result["severity"] == "not_assessed"
    assert result["urgent"] is None
    assert "could not retrieve" in result["response"]
    assert "diagnos" not in result["response"].lower()
