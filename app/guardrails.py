def input_guardrails(message: str):
    blocked_words = ["ssn", "account number"]
    for w in blocked_words:
        if w in message.lower():
            return False, "PII detected"
    return True, message

def output_guardrails(text: str, risk_level: str):
    if risk_level == "HIGH":
        return (
            "I can’t provide direct investment instructions. "
            "I can explain concepts or help you understand options instead.\n\n"
            + text
        )
    return text
