
from fastapi import FastAPI

app = FastAPI(
    title="NLIC Chatbot API",
    version="0.1.0",
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "message": "NLIC Chatbot backend is running",
    }
