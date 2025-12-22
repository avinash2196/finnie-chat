from app.env import load_env_once

# Ensure .env is loaded before other imports need the keys
load_env_once()

from fastapi import FastAPI
from pydantic import BaseModel
from app.guardrails import input_guardrails, output_guardrails
from app.agents.orchestrator import handle_message
from app.llm import get_gateway_metrics
from app.memory import get_memory
import uuid

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None  # Optional; generates new if not provided

@app.post("/chat")
def chat(req: ChatRequest):
    # Use provided conversation_id or generate new one
    conversation_id = req.conversation_id or str(uuid.uuid4())
    
    ok, msg = input_guardrails(req.message)
    if not ok:
        return {
            "reply": msg,
            "conversation_id": conversation_id,
            "intent": None,
            "risk": None
        }

    # Get conversation context from memory
    memory = get_memory()
    context = memory.get_context(conversation_id, limit=10)

    # Handle message with context
    reply, intent, risk = handle_message(msg, conversation_context=context)
    reply = output_guardrails(reply, risk)

    # Store in conversation memory
    memory.add_message(conversation_id, role="user", content=req.message, intent=intent, risk=risk)
    memory.add_message(conversation_id, role="assistant", content=reply)

    return {
        "reply": reply,
        "conversation_id": conversation_id,
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
