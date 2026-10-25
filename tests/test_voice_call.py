"""Contract tests for the simulated call API; cloud STT/LLM/TTS are mocked."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core import ai_engine
from app.ai.generator import GenerationUnavailableError
from app.core.config import settings
from app.integrations.ethio_healthbridge import emergency
from app.api import voice_call


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


SOURCES = [{
    "id": "case-1",
    "topic": "Fever",
    "population": "Adult",
    "page": 135,
    "source": "Ethiopian Primary Health Care Clinical Guidelines, 2017",
    "content": "Guideline excerpt: assess the patient with fever using the relevant clinical assessment section.",
    "similarity": 0.81,
}]


def test_red_flag_check_is_local_and_has_english_and_amharic_phrases():
    assert emergency.detect_red_flag("I have severe chest pain")
    assert emergency.detect_red_flag("የመተንፈስ ችግር አለኝ")
    assert emergency.detect_red_flag("I have a headache") is None


def test_emergency_short_circuits_retrieval_and_generation(monkeypatch):
    def should_not_run(*args, **kwargs):
        raise AssertionError("red flag must short-circuit retrieval")

    monkeypatch.setattr(ai_engine, "search_clinical_guidelines", should_not_run)
    monkeypatch.setattr(ai_engine, "generate_grounded_response", should_not_run)
    result = ai_engine.generate_health_response("I have chest pain", language="en")
    assert result["urgent"] is True
    assert result["evidence_status"] == "safety_rule_triggered"
    assert result["sources"] == []
    assert "does not call emergency services" in result["response"].lower()


def test_text_turn_returns_actual_response_and_sources(client, monkeypatch, tmp_path):
    async def fake_tts(text, language="am"):
        path = tmp_path / "response_test.mp3"
        path.write_bytes(b"fake-mp3-for-contract-test")
        monkeypatch.setattr(voice_call, "AUDIO_DIR", tmp_path)
        return str(path)

    monkeypatch.setattr(voice_call, "generate_health_response", lambda *a, **k: {
        "response": "A grounded response from the mocked service.",
        "language": "en", "severity": "not_assessed", "urgent": None,
        "evidence_status": "retrieved", "sources": SOURCES,
        "disclaimer": "Prototype only.", "generation_mode": "gemini_grounded",
    })
    monkeypatch.setattr(voice_call, "generate_voice_response", fake_tts)

    response = client.post("/api/call/text", json={"message": "What should I know about fever?", "language": "en"})
    assert response.status_code == 200
    body = response.json()
    assert body["transcription"] == "What should I know about fever?"
    assert body["response"] == "A grounded response from the mocked service."
    assert body["sources"][0]["page"] == 135
    assert body["generation_mode"] == "gemini_grounded"
    assert body["audio_url"] == "/api/call/audio/response_test.mp3"
    audio = client.get(body["audio_url"])
    assert audio.status_code == 200
    assert audio.content == b"fake-mp3-for-contract-test"


def test_voice_upload_transcribes_then_returns_response(client, monkeypatch, tmp_path):
    async def fake_tts(text, language="am"):
        path = tmp_path / "response_voice.mp3"
        path.write_bytes(b"mock-audio")
        monkeypatch.setattr(voice_call, "AUDIO_DIR", tmp_path)
        return str(path)

    monkeypatch.setattr(voice_call, "transcribe_audio", lambda path, language="am": "ትኩሳት አለኝ")
    monkeypatch.setattr(voice_call, "generate_health_response", lambda *a, **k: {
        "response": "የተመለሰ ምላሽ።", "language": "am", "severity": "not_assessed",
        "urgent": None, "evidence_status": "retrieved", "sources": SOURCES,
        "disclaimer": "Prototype only.", "generation_mode": "gemini_grounded",
    })
    monkeypatch.setattr(voice_call, "generate_voice_response", fake_tts)

    response = client.post(
        "/api/call/voice",
        data={"language": "am", "history_json": "[]"},
        files={"audio": ("recording.webm", b"synthetic-audio", "audio/webm;codecs=opus")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["transcription"] == "ትኩሳት አለኝ"
    assert body["response"] == "የተመለሰ ምላሽ።"
    assert body["sources"][0]["source"].startswith("Ethiopian Primary")
    assert body["audio_available"] is True


def test_voice_rejects_unsupported_mime_type(client):
    response = client.post(
        "/api/call/voice",
        data={"language": "am", "history_json": "[]"},
        files={"audio": ("recording.exe", b"data", "application/x-msdownload")},
    )
    assert response.status_code == 415


def test_voice_rejects_oversized_upload(client, monkeypatch):
    monkeypatch.setattr(voice_call, "MAX_AUDIO_BYTES", 4)
    response = client.post(
        "/api/call/voice",
        data={"language": "am", "history_json": "[]"},
        files={"audio": ("recording.webm", b"12345", "audio/webm")},
    )
    assert response.status_code == 413


def test_amharic_text_turn_reports_missing_gemini_key(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "enable_generative", True)
    monkeypatch.setattr(voice_call, "generate_health_response", ai_engine.generate_health_response)
    monkeypatch.setattr(ai_engine, "search_clinical_guidelines", lambda *a, **k: SOURCES)
    response = client.post("/api/call/text", json={"message": "ትኩሳት አለኝ", "language": "am"})
    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]


def test_audio_endpoint_rejects_path_traversal(client):
    response = client.get("/api/call/audio/..%2F..%2F.env")
    assert response.status_code in (404, 405)


def test_followup_history_is_accepted_and_forwarded(client, monkeypatch):
    seen = {}

    def fake_response(message, language="en", history=None):
        seen["message"] = message
        seen["history"] = history
        return {"response": "Follow-up answer", "language": language, "severity": "not_assessed",
                "urgent": None, "evidence_status": "insufficient", "sources": [], "disclaimer": "Prototype"}

    async def no_tts(text, language="en"):
        return ""

    monkeypatch.setattr(voice_call, "generate_health_response", fake_response)
    monkeypatch.setattr(voice_call, "generate_voice_response", no_tts)
    response = client.post("/api/call/text", json={
        "message": "What about children?", "language": "en",
        "history": [{"role": "user", "content": "Tell me about fever"}, {"role": "assistant", "content": "Guideline excerpt."}],
    })
    assert response.status_code == 200
    assert seen["message"] == "What about children?"
    assert len(seen["history"]) == 2
    assert response.json()["audio_available"] is False


def test_amharic_voice_without_key_fails_explicitly(monkeypatch, tmp_path):
    from app.integrations.ethio_healthbridge import stt_engine
    audio_path = tmp_path / "short.webm"
    audio_path.write_bytes(b"synthetic audio")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        stt_engine.transcribe_audio(str(audio_path), language="am")


def test_phone_call_interface_is_served_and_uses_real_api_routes(client):
    response = client.get("/app")
    assert response.status_code == 200
    page = response.text
    assert "Simulated patient call" in page
    assert "getUserMedia" in page
    assert "MediaRecorder" in page
    assert "/api/call/voice" in page
    assert "/api/call/text" in page
    assert "Guideline evidence" in page
    assert "does not call ambulances or emergency services" in page
