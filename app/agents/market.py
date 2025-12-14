import json
from app.llm import call_llm
from app.mcp.market import get_quote


TICKER_EXTRACT_PROMPT = """
Extract the stock ticker symbol from the user query.

Rules:
- Return ONLY the ticker symbol.
- Use uppercase.
- If no ticker is found, return null.

Examples:
"What is SPY doing today?" -> SPY
"How is Apple stock today?" -> AAPL
"What is the market doing?" -> null

Respond ONLY in JSON:
{
  "ticker": "SPY" | null
}
"""


def extract_ticker(query: str):
    result = call_llm(
        system_prompt=TICKER_EXTRACT_PROMPT,
        user_prompt=query,
        temperature=0
    )

    try:
        parsed = json.loads(result)
        return parsed.get("ticker")
    except Exception:
        return None


def run(query: str):
    ticker = extract_ticker(query)

    if not ticker:
        return "I couldn’t identify a stock ticker in your question."

    data = get_quote(ticker)

    if not data or not data.get("price"):
        return f"Market data is currently unavailable for {ticker}."

    return (
        f"{ticker} is trading at {data['price']} {data['currency']} "
        f"({data['change_pct']:.2f}% today)."
    )
