"""
Market data client and MCP integration.
Provides typed access to market quotes via the MCP server.
"""

import time
from dataclasses import dataclass
from typing import Optional
from app.mcp.market_server import get_server as get_market_server


@dataclass
class MarketQuote:
    """Typed market quote response."""
    ticker: str
    price: Optional[float]
    currency: Optional[str]
    change_pct: Optional[float]
    timestamp: float
    source: str = "yfinance"
    error: Optional[str] = None


class MarketClient:
    """Client for market data with caching."""

    def __init__(self, ttl_seconds: int = 30):
        """Initialize market client.
        
        Args:
            ttl_seconds: Cache TTL for quotes in seconds.
        """
        self._server = get_market_server()
        self._cache = {}
        self._ttl = ttl_seconds

    def _is_fresh(self, key: str) -> bool:
        """Check if cache entry is fresh."""
        entry = self._cache.get(key)
        return entry and (time.time() - entry["ts"] < self._ttl)

    def get_quote(self, ticker: str) -> Optional[MarketQuote]:
        """Fetch stock quote with caching.
        
        Args:
            ticker: Stock ticker symbol.
            
        Returns:
            MarketQuote or None if unavailable.
        """
        key = ticker.upper()
        if self._is_fresh(key):
            return self._cache[key]["quote"]

        try:
            result = self._server.call_tool("get_quote", {"ticker": ticker})
            quote = MarketQuote(
                ticker=result["ticker"],
                price=result.get("price"),
                currency=result.get("currency"),
                change_pct=result.get("change_pct"),
                timestamp=time.time(),
                error=result.get("error")
            )
            self._cache[key] = {"ts": time.time(), "quote": quote}
            return quote
        except Exception as e:
            return MarketQuote(
                ticker=key,
                price=None,
                currency=None,
                change_pct=None,
                timestamp=time.time(),
                error=str(e)
            )


# Singleton client instance
_client: Optional[MarketClient] = None


def get_client() -> MarketClient:
    """Get or create the market client."""
    global _client
    if _client is None:
        _client = MarketClient()
    return _client

