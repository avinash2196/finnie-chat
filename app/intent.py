import json
from app.llm import call_llm

INTENT_SYSTEM_PROMPT = """
You are an intent classifier for a financial assistant.

Classify the user message into ONE of:
- ASK_CONCEPT: Asking to explain a financial concept (bonds, diversification, etc.)
- ASK_MARKET: Asking for live market data (price, trend, volume)
- ASK_PORTFOLIO: Asking about their holdings (diversification, allocation, concentration)
- ASK_RISK: Asking about portfolio risk, volatility, or Sharpe ratio
- ASK_STRATEGY: Asking for investment opportunities or screening (dividend, growth, value)
- ADVICE: Asking for direct trading advice (buy/sell specific stock, allocation target)
- OTHER: General chat, small talk, or unrelated questions

Also assign risk level:
- LOW (education, definitions, general explanations)
- MED (strategy discussion, comparisons, portfolio analysis)
- HIGH (direct buy/sell, tax, legal, urgent, specific recommendations)

Rules:
- If message contains "diversify", "allocation", "concentration", "rebalance" → ASK_PORTFOLIO
- If message contains "risk", "volatility", "sharpe", "beta", "downside" → ASK_RISK
- If message contains "dividend", "growth", "value", "screen", "find stocks" → ASK_STRATEGY
- If message contains "should I buy", "which stock", "how much" with specific action → ADVICE

Respond ONLY in valid JSON:
{
  "intent": "ASK_CONCEPT|ASK_MARKET|ASK_PORTFOLIO|ASK_RISK|ASK_STRATEGY|ADVICE|OTHER",
  "risk": "LOW|MED|HIGH"
}
"""

def classify_intent(message: str):
    output = call_llm(INTENT_SYSTEM_PROMPT, message)
    parsed = json.loads(output)
    return parsed["intent"], parsed["risk"]
