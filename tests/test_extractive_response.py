from app.core.ai_engine import compose_extractive_response


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
