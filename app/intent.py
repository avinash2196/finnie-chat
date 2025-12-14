import json
from app.llm import call_llm

INTENT_SYSTEM_PROMPT = """
You are an intent classifier for a financial education assistant.

Classify the user message into:
- ASK_CONCEPT
- ASK_MARKET
- ASK_PORTFOLIO
- ADVICE
- OTHER

Also assign risk level:
- LOW (education, definitions)
- MED (strategy discussion, comparisons)
- HIGH (direct buy/sell, tax, legal, urgent)

Respond ONLY in valid JSON:
{
  "intent": "...",
  "risk": "LOW|MED|HIGH"
}
"""

def classify_intent(message: str):
    output = call_llm(INTENT_SYSTEM_PROMPT, message)
    parsed = json.loads(output)
    return parsed["intent"], parsed["risk"]
