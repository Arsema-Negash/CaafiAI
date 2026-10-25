import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core import ai_engine


@pytest.fixture
def client():
    # Use the context-managed client so Starlette can close the httpx transport.
    with TestClient(app) as test_client:
        yield test_client


FAKE_RESULTS = [
    {
        "id": 17,
        "topic": "Fever",
        "population": "Child",
        "page": 135,
        "source": "Ethiopian Primary Health Care Clinical Guidelines, 2017",
        "content": "Example guideline passage for a unit test.",
        "score": 0.82,
        "ranking_score": 0.9,
    }
]


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_endpoint_has_boolean(client):
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["ready"], bool)
    assert body["embedding_model"] == "all-MiniLM-L6-v2"


def test_consultation_returns_source_linked_evidence(client, monkeypatch):
    monkeypatch.setattr(ai_engine, "search_clinical_guidelines", lambda query, top_k: FAKE_RESULTS)

    response = client.post(
        "/api/consultation",
        json={"message": "What should I know about fever in a child?", "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["severity"] == "not_assessed"
    assert body["urgent"] is None
    assert body["evidence_status"] == "retrieved"
    assert body["sources"][0]["page"] == 135
    assert body["sources"][0]["source"].startswith("Ethiopian Primary")
    assert "not a diagnosis" in body["response"]
    assert body["disclaimer"]


def test_blank_message_is_rejected(client):
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 422


def test_missing_index_returns_service_unavailable(client, monkeypatch):
    def missing_index(query, top_k):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(ai_engine, "search_clinical_guidelines", missing_index)
    response = client.post("/chat", json={"message": "fever"})
    assert response.status_code == 503


def test_non_english_language_is_rejected_for_now(client):
    response = client.post(
        "/chat",
        json={"message": "Question about fever", "language": "am"},
    )
    assert response.status_code == 422


def test_chat_endpoint_returns_evidence_and_does_not_assess_urgency(client, monkeypatch):
    monkeypatch.setattr(
        ai_engine,
        "search_clinical_guidelines",
        lambda query, top_k: FAKE_RESULTS,
    )

    response = client.post(
        "/chat",
        json={"message": "What should I know about fever in a child?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["urgent"] is None
    assert body["severity"] == "not_assessed"
    assert body["evidence_status"] == "retrieved"
    assert len(body["sources"]) == 1
    assert body["sources"][0]["page"] == 135


def test_root_endpoint_returns_service_info(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "CAAFI_AI"
    assert "guideline" in data
    assert "notice" in data


def test_message_exceeding_max_length_is_rejected(client):
    too_long = "a" * 2001
    response = client.post("/chat", json={"message": too_long})
    assert response.status_code == 422


def test_runtime_error_returns_service_unavailable(client, monkeypatch):
    def boom(query, top_k):
        raise RuntimeError("Sentence transformer failed to load.")

    monkeypatch.setattr(ai_engine, "search_clinical_guidelines", boom)
    response = client.post("/chat", json={"message": "fever in an adult"})
    assert response.status_code == 503
    assert response.json()["detail"] == "The retrieval service is temporarily unavailable."
    assert "Sentence transformer" not in response.json()["detail"]


def test_readiness_reports_missing_when_index_absent(client, monkeypatch, tmp_path):
    missing_path = tmp_path / "nonexistent.json"
    import app.ai.retrieval as ret
    monkeypatch.setattr(ret, "EMBEDDINGS_FILE", missing_path)

    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is False
    assert data["clinical_index"] == "missing"


def test_malformed_json_is_rejected(client):
    response = client.post(
        "/chat",
        content="{not-json",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422


def test_empty_retrieval_does_not_claim_diagnosis_or_urgency(client, monkeypatch):
    monkeypatch.setattr(ai_engine, "search_clinical_guidelines", lambda query, top_k: [])
    response = client.post("/chat", json={"message": "What is the capital of France?"})
    assert response.status_code == 200
    body = response.json()
    assert body["evidence_status"] == "insufficient"
    assert body["sources"] == []
    assert body["severity"] == "not_assessed"
    assert body["urgent"] is None
    assert "could not retrieve" in body["response"].lower()
    lowered = (body["response"] + body["disclaimer"]).lower()
    assert "confirmed diagnosis" not in lowered
    assert "you have been diagnosed" not in lowered


def test_privacy_safeguard_logs_char_count_not_patient_query(client, monkeypatch, caplog):
    monkeypatch.setattr(ai_engine, "search_clinical_guidelines", lambda query, top_k: FAKE_RESULTS)
    unique_sensitive_text = "SENSITIVE_PATIENT_IDENTIFIER_XYZ123"

    with caplog.at_level("INFO"):
        response = client.post("/chat", json={"message": unique_sensitive_text})

    assert response.status_code == 200
    # The sensitive clinical query itself must never appear in application logs
    assert unique_sensitive_text not in caplog.text
    # But operational metadata (query_chars) must be safely logged
    assert f"query_chars={len(unique_sensitive_text)}" in caplog.text
