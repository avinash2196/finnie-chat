import json
from app.llm import call_llm
from app.mcp.market import get_client


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

_client = get_client()


def extract_ticker(query: str):
    """Extract stock ticker from user query using LLM."""
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
    """Market agent: fetch and format stock quote."""
    ticker = extract_ticker(query)

    if not ticker:
        return "I couldn't identify a stock ticker in your question."

    quote = _client.get_quote(ticker)

    if not quote or quote.price is None:
        error_msg = quote.error if quote and quote.error else "unknown error"
        return f"Market data unavailable for {ticker}: {error_msg}"

    return (
        f"{ticker} is trading at {quote.price} {quote.currency} "
        f"({quote.change_pct:.2f}% today)."
    )
