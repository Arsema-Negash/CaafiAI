from fastapi.testclient import TestClient

from app.main import app
from app.core import ai_engine

client = TestClient(app)


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


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_endpoint_has_boolean():
    response = client.get("/ready")
    assert response.status_code == 200
    assert isinstance(response.json()["ready"], bool)


def test_consultation_returns_source_linked_evidence(monkeypatch):
    monkeypatch.setattr(ai_engine, "search_clinical_guidelines", lambda query, top_k: FAKE_RESULTS)

    response = client.post(
        "/api/consultation",
        json={"message": "What should I know about fever in a child?", "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["severity"] == "not_assessed"
    assert body["urgent"] is None
    assert body["sources"][0]["page"] == 135
    assert body["sources"][0]["source"].startswith("Ethiopian Primary")
    assert "not a diagnosis" in body["response"]
    assert body["disclaimer"]


def test_blank_message_is_rejected():
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 422


def test_missing_index_returns_service_unavailable(monkeypatch):
    def missing_index(query, top_k):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(ai_engine, "search_clinical_guidelines", missing_index)
    response = client.post("/chat", json={"message": "fever"})
    assert response.status_code == 503


def test_non_english_language_is_rejected_for_now():
    response = client.post(
        "/chat",
        json={"message": "Question about fever", "language": "am"},
    )
    assert response.status_code == 422


def test_chat_endpoint_returns_evidence_and_does_not_assess_urgency(monkeypatch):
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
    assert len(body["sources"]) == 1
    assert body["sources"][0]["page"] == 135
