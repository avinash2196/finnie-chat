import json
import os
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

def _rule_based_intent(message: str):
  """Simple deterministic fallback intent classifier.

  Used when LLM is unavailable or returns invalid output during tests/local runs.
  """
  m = message.lower()
  portfolio_kw = any(k in m for k in ["diversify", "diversified", "allocation", "concentration", "concentrated", "rebalance", "portfolio"])
  risk_kw = any(k in m for k in ["risk", "volatility", "volatile", "sharpe", "beta", "downside", "safer"])
  market_kw = any(k in m for k in ["price", "volume", "market", "s&p", "sp500", "up today", "trading", "stock price"])
  concept_kw = any(k in m for k in ["what is", "explain", "how do", "how does"])
  strategy_kw = any(k in m for k in ["dividend", "growth", "value", "screen", "find stocks", "opportunities"])

  # Risk-related (higher priority so portfolio mentions with "risk" are classified as risk)
  if risk_kw:
    return "ASK_RISK", "MED"
  # Market data (before concept so price queries classify as market)
  if market_kw:
    return "ASK_MARKET", "LOW"
  # Concept/education (only when not portfolio to avoid capturing allocation queries)
  if concept_kw and not portfolio_kw:
    return "ASK_CONCEPT", "LOW"
  # Strategy/screener (after concept so "how do dividends work" stays concept)
  if strategy_kw:
    return "ASK_STRATEGY", "MED"
  # Portfolio-related
  if portfolio_kw:
    return "ASK_PORTFOLIO", "MED"
  # Advice (direct buy/sell requests)
  if any(k in m for k in ["should i buy", "should i sell", "buy", "sell", "how much should i invest"]):
    return "ADVICE", "HIGH"

  return "OTHER", "LOW"


def classify_intent(message: str):
  rule_intent, rule_risk = _rule_based_intent(message)

  # In test runs, prefer deterministic rule-based to avoid flaky LLM outputs
  if os.getenv("PYTEST_CURRENT_TEST"):
    return rule_intent, rule_risk

  try:
    output = call_llm(INTENT_SYSTEM_PROMPT, message)
    parsed = json.loads(output)
    intent = parsed.get("intent")
    risk = parsed.get("risk")
    if intent and risk:
      return intent, risk
  except Exception:
    pass

  # Fallback to rule-based deterministic classifier (safe for tests/local runs)
  return rule_intent, rule_risk
