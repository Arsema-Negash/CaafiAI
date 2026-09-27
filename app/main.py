from fastapi import FastAPI

app = FastAPI(title="CaafiAI")


@app.get("/health")
def health_check():
    return {"status": "CaafiAI is running"}