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
    try:
        result = call_llm(
            system_prompt=TICKER_EXTRACT_PROMPT,
            user_prompt=query,
            temperature=0
        )

        parsed = json.loads(result)
        ticker = parsed.get("ticker")
        if ticker:
            return ticker
    except Exception:
        pass

    # Heuristic fallback when LLM is unavailable
    m = query.lower()
    common = {
        "apple": "AAPL",
        "aapl": "AAPL",
        "tesla": "TSLA",
        "tsla": "TSLA",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "microsoft": "MSFT",
        "msft": "MSFT",
        "amazon": "AMZN",
        "amzn": "AMZN",
        "nvidia": "NVDA",
        "nvda": "NVDA",
        "s&p": "SPY",
        "s&p 500": "SPY",
        "sp500": "SPY",
        "s&p500": "SPY",
        "spy": "SPY",
    }
    for key, ticker in common.items():
        if key in m:
            return ticker

    # Try grabbing the first uppercase token as a last resort
    for token in query.replace("?", "").replace(",", " ").split():
        if token.isupper() and 1 <= len(token) <= 5:
            return token

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


def get_market_data(ticker: str):
    """Lightweight getter used by API endpoints to fetch quote details."""
    quote = _client.get_quote(ticker)
    if not quote or quote.price is None:
        return None

    # Basic shape expected by FastAPI endpoints
    return {
        "ticker": quote.ticker,
        "price": quote.price,
        "currency": quote.currency,
        "change_pct": quote.change_pct,
        # MarketClient currently does not return these; keep placeholders
        "change": None,
        "volume": None,
        "market_cap": None,
        "timestamp": quote.timestamp,
        "source": quote.source,
        "error": quote.error,
    }
