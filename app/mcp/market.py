"""
Market data client and MCP integration.
Provides typed access to market quotes via the MCP server.
"""
import os
import json
import time
from dataclasses import dataclass
from typing import Optional, List, Dict
from app.mcp.market_server import get_server as get_market_server

try:  # Redis optional
    import redis  # type: ignore
except Exception:
    redis = None


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
    """Client for market data with short-TTL in-memory caching and batch fetch support."""

    def __init__(self, ttl_seconds: int = 5, redis_ttl_seconds: int = 5):
        """Initialize market client.

        Args:
            ttl_seconds: Cache TTL for quotes in seconds (default short TTL).
        """
        self._server = get_market_server()
        self._cache: Dict[str, Dict] = {}
        self._ttl = ttl_seconds
        self._redis = self._init_redis()
        self._redis_ttl = redis_ttl_seconds

    def _init_redis(self):
        url = os.getenv("REDIS_URL")
        if not (redis and url):
            return None
        try:
            client = redis.Redis.from_url(url)
            client.ping()
            return client
        except Exception:
            return None

    def _is_fresh(self, key: str) -> bool:
        """Check if cache entry is fresh."""
        entry = self._cache.get(key)
        return bool(entry and (time.time() - entry.get("ts", 0) < self._ttl))

    def _serialize_quote(self, quote: "MarketQuote") -> str:
        return json.dumps({
            "ticker": quote.ticker,
            "price": quote.price,
            "currency": quote.currency,
            "change_pct": quote.change_pct,
            "timestamp": quote.timestamp,
            "source": quote.source,
            "error": quote.error,
        })

    def _deserialize_quote(self, payload: str) -> Optional["MarketQuote"]:
        try:
            data = json.loads(payload)
            if data.get("price") is None and data.get("error"):
                return None
            return MarketQuote(
                ticker=data.get("ticker"),
                price=data.get("price"),
                currency=data.get("currency"),
                change_pct=data.get("change_pct"),
                timestamp=data.get("timestamp", time.time()),
                source=data.get("source", "yfinance"),
                error=data.get("error"),
            )
        except Exception:
            return None

    def get_quote(self, ticker: str) -> Optional[MarketQuote]:
        """Fetch a single stock quote with caching."""
        key = ticker.upper()
        if self._is_fresh(key):
            return self._cache[key]["quote"]

        if self._redis:
            try:
                cached = self._redis.get(f"quote:{key}")
                if cached:
                    q = self._deserialize_quote(cached.decode("utf-8"))
                    if q and q.price is not None:
                        self._cache[key] = {"ts": time.time(), "quote": q}
                        return q
            except Exception:
                pass

        try:
            result = self._server.call_tool("get_quote", {"ticker": ticker})
            quote = MarketQuote(
                ticker=result.get("ticker", key),
                price=result.get("price"),
                currency=result.get("currency"),
                change_pct=result.get("change_pct"),
                timestamp=time.time(),
                error=result.get("error")
            )
            if quote.price is not None and not quote.error:
                self._cache[key] = {"ts": time.time(), "quote": quote}
                if self._redis:
                    try:
                        self._redis.setex(f"quote:{key}", self._redis_ttl, self._serialize_quote(quote))
                    except Exception:
                        pass
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

    def get_quotes(self, tickers: List[str]) -> Dict[str, MarketQuote]:
        """Fetch multiple quotes using cache where possible and batch for misses.

        Returns a dict mapping UPPER ticker -> MarketQuote.
        """
        now = time.time()
        result: Dict[str, MarketQuote] = {}
        to_fetch: List[str] = []

        # Use cache where fresh
        for t in tickers:
            key = t.upper()
            if self._is_fresh(key):
                result[key] = self._cache[key]["quote"]
                continue

            if self._redis:
                try:
                    cached = self._redis.get(f"quote:{key}")
                    if cached:
                        q = self._deserialize_quote(cached.decode("utf-8"))
                        if q and q.price is not None:
                            self._cache[key] = {"ts": now, "quote": q}
                            result[key] = q
                            continue
                except Exception:
                    pass

            to_fetch.append(key)

        if to_fetch:
            try:
                raw = self._server.call_tool("get_quotes", {"tickers": to_fetch})
                # raw expected as mapping ticker->dict
                for k, v in (raw or {}).items():
                    quote = MarketQuote(
                        ticker=k,
                        price=v.get("price"),
                        currency=v.get("currency"),
                        change_pct=v.get("change_pct"),
                        timestamp=time.time(),
                        error=v.get("error")
                    )
                    if quote.price is not None and not quote.error:
                        self._cache[k] = {"ts": now, "quote": quote}
                        if self._redis:
                            try:
                                self._redis.setex(f"quote:{k}", self._redis_ttl, self._serialize_quote(quote))
                            except Exception:
                                pass
                    result[k] = quote
            except Exception as e:
                # If batch fetch fails, populate errors for each requested ticker
                for k in to_fetch:
                    result[k] = MarketQuote(ticker=k, price=None, currency=None, change_pct=None, timestamp=time.time(), error=str(e))

        return result


# Singleton client instance
_client: Optional[MarketClient] = None


def get_client() -> MarketClient:
    """Get or create the market client."""
    global _client
    if _client is None:
        _client = MarketClient()
    return _client

