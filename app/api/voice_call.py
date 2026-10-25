"""Simulated browser phone-call API: text/audio in, evidence-grounded answer out."""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from app.ai.generator import GenerationUnavailableError
from app.core.ai_engine import generate_health_response
from app.integrations.ethio_healthbridge.stt_engine import transcribe_audio
from app.integrations.ethio_healthbridge.tts_engine import AUDIO_DIR, generate_voice_response

logger = logging.getLogger("caafi_ai.voice_call")
router = APIRouter(prefix="/api/call", tags=["simulated voice call"])
MAX_AUDIO_BYTES = 15 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/ogg", "audio/wav", "audio/x-wav", "audio/mpeg",
    "audio/mp4", "audio/aac", "audio/mp3", "application/octet-stream",
}


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1000)


class TextTurnRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: Literal["en", "am"] = "en"
    history: list[Turn] = Field(default_factory=list, max_length=6)

    @field_validator("message")
    @classmethod
    def nonblank_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be blank.")
        return value.strip()


def _answer(message: str, language: str, history: list[dict[str, str]]) -> dict:
    try:
        result = generate_health_response(message, language=language, history=history)
    except GenerationUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="The clinical guideline index is missing. Restore/build the CAAFI_AI index before consulting.") from exc
    except RuntimeError as exc:
        logger.warning("Call turn unavailable: error_type=%s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="The guideline retrieval or AI service is temporarily unavailable.") from exc
    return result


async def _synthesize(response: dict, language: str) -> dict:
    try:
        path = await generate_voice_response(response["response"], language=language)
    except Exception as exc:  # audio is optional; text/evidence should remain available
        logger.warning("TTS unavailable: error_type=%s", type(exc).__name__)
        path = ""
    response["audio_url"] = f"/api/call/audio/{Path(path).name}" if path else None
    response["audio_available"] = bool(path)
    return response


@router.post("/text", summary="Handle one typed turn during a simulated call")
async def text_turn(request: TextTurnRequest) -> dict:
    history = [turn.model_dump() for turn in request.history]
    result = _answer(request.message, request.language, history)
    result["transcription"] = request.message
    return await _synthesize(result, request.language)


@router.post("/voice", summary="Transcribe a voice clip, answer from guideline evidence, and synthesize speech")
async def voice_turn(
    audio: UploadFile = File(...),
    language: Literal["am", "en"] = Form("am"),
    history_json: str = Form("[]"),
) -> dict:
    if audio.content_type and audio.content_type.lower().split(";")[0].strip() not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported audio format. Use the browser's recorded WebM/Opus audio or WAV/MP3.")
    try:
        import json
        parsed_history = json.loads(history_json)
        if not isinstance(parsed_history, list) or len(parsed_history) > 6:
            raise ValueError
        history = [Turn.model_validate(item).model_dump() for item in parsed_history]
    except Exception as exc:
        raise HTTPException(status_code=422, detail="history_json must be a JSON list of up to six user/assistant turns.") from exc

    # Enforce size while streaming; do not trust the client-provided Content-Length.
    suffix = Path(audio.filename or "recording.webm").suffix.lower()
    if suffix not in {".webm", ".wav", ".mp3", ".mp4", ".m4a", ".ogg", ".aac", ".flac"}:
        suffix = ".webm"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="caafi_audio_", suffix=suffix, delete=False) as tmp:
            temp_path = tmp.name
            size = 0
            while True:
                chunk = await audio.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_AUDIO_BYTES:
                    raise HTTPException(status_code=413, detail="Audio clip exceeds the 15 MB limit. Please record a shorter question.")
                tmp.write(chunk)
        if size == 0:
            raise HTTPException(status_code=422, detail="The audio clip is empty. Please record your question again.")
        try:
            transcript = transcribe_audio(temp_path, language=language)
        except RuntimeError as exc:
            message = str(exc)
            status = 503 if "GEMINI_API_KEY" in message or "service" in message.lower() else 502
            raise HTTPException(status_code=status, detail=message) from exc
        result = _answer(transcript, language, [turn.model_dump() for turn in history])
        result["transcription"] = transcript
        return await _synthesize(result, language)
    finally:
        await audio.close()
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


@router.get("/audio/{filename}", summary="Play generated call audio")
def call_audio(filename: str) -> FileResponse:
    # Only generated filenames from this service are accepted; never join arbitrary paths.
    if not filename.startswith("response_") or Path(filename).name != filename or not filename.endswith(".mp3"):
        raise HTTPException(status_code=404, detail="Audio not found.")
    audio_path = AUDIO_DIR / filename
    if not audio_path.is_file():
        raise HTTPException(status_code=404, detail="Audio not found or expired.")
    return FileResponse(audio_path, media_type="audio/mpeg")
