from fastapi import FastAPI
from pydantic import BaseModel

from app.health import generate_health_response


app = FastAPI(title="CAAFI_AI")


class ChatRequest(BaseModel):
    message: str
    language: str = "en"


class ChatResponse(BaseModel):
    response: str
    language: str
    severity: str
    urgent: bool


@app.get("/health")
def health_check():
    return {"status": "CAAFI_AI is running"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    result = generate_health_response(request.message)

    return ChatResponse(
        response=result["response"],
        language=request.language,
        severity=result["severity"],
        urgent=result["urgent"],
    )