from app.orchestrator import handle_message

def chat_system(input_text: str) -> str:
    reply, intent, risk = handle_message(input_text)
    return reply
