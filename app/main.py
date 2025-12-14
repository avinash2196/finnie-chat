import os
from pathlib import Path

# Load environment variables from .env file FIRST (no external dependency)
def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    os.environ[key.strip()] = value.strip()

load_env()

from fastapi import FastAPI
from pydantic import BaseModel
from app.guardrails import input_guardrails, output_guardrails
from app.agents.orchestrator import handle_message
from app.llm import get_gateway_metrics

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    ok, msg = input_guardrails(req.message)
    if not ok:
        return {"reply": msg}

    reply, intent, risk = handle_message(msg)
    reply = output_guardrails(reply, risk)

    return {
        "reply": reply,
        "intent": intent,
        "risk": risk
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    """Get gateway metrics (cache hit rate, failures, etc.)."""
    return get_gateway_metrics()
