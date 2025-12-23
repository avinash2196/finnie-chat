"""
MCP Server for market data operations.
Implements tools for fetching stock quotes, market trends, and portfolio data.
"""

import json
import logging
import time
from typing import Any
import yfinance as yf
from app.observability import observability
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketTool:
    """Base class for market tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def to_schema(self) -> dict:
        """Return tool schema for MCP."""
        raise NotImplementedError


class GetQuoteTool(MarketTool):
    """Tool for fetching stock quotes."""

    def __init__(self):
        super().__init__(
            name="get_quote",
            description="Fetch current stock quote including price, change, and currency."
        )

    def to_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, SPY)"
                    }
                },
                "required": ["ticker"]
            }
        }

    def execute(self, ticker: str) -> dict:
        """Fetch quote for ticker."""
        start = time.time()
        try:
            t = yf.Ticker(ticker.upper())
            info = t.info or {}
            price = info.get("regularMarketPrice")
            currency = info.get("currency") or info.get("financialCurrency") or "USD"
            prev_close = info.get("regularMarketPreviousClose")
            
            change_pct = None
            if price is not None and prev_close is not None:
                change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else None

            result = {
                "ticker": ticker.upper(),
                "price": price,
                "currency": currency,
                "change_pct": round(change_pct, 2) if change_pct is not None else None,
                "timestamp": info.get("regularMarketTime"),
                "source": "yfinance"
            }
            return result
        except Exception as e:
            logger.error(f"Error fetching quote for {ticker}: {e}")
            return {
                "ticker": ticker.upper(),
                "price": None,
                "currency": None,
                "change_pct": None,
                "error": str(e),
                "source": "yfinance"
            }
        finally:
            duration_ms = (time.time() - start) * 1000
            try:
                observability.track_metric("market_yfinance_call_ms", duration_ms, {"ticker": ticker})
                logger.info(f"yfinance fetch for {ticker.upper()} took {duration_ms:.2f}ms")
            except Exception:
                pass


class GetQuotesTool(MarketTool):
    """Tool for fetching multiple stock quotes in a single batch."""

    def __init__(self):
        super().__init__(
            name="get_quotes",
            description="Fetch current stock quotes for multiple tickers in a batch."
        )

    def to_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ticker symbols"
                    }
                },
                "required": ["tickers"]
            }
        }

    def execute(self, tickers: list) -> dict:
        """Fetch quotes for a list of tickers using yf.Tickers for batching."""
        start = time.time()
        results = {}
        try:
            # yfinance supports bulk tickers via Tickers; create shared multi object
            symbols = " ".join([t.upper() for t in tickers])
            multi = yf.Tickers(symbols)

            # Use a small ThreadPoolExecutor to parallelize per-ticker info extraction
            max_workers = min(8, len(tickers)) if tickers else 1

            def fetch_one(sym: str):
                max_attempts = 3
                for attempt in range(1, max_attempts + 1):
                    try:
                        tk = multi.tickers.get(sym.upper())
                        info = getattr(tk, "info", {}) or {}
                        price = info.get("regularMarketPrice")
                        currency = info.get("currency") or info.get("financialCurrency") or "USD"
                        prev_close = info.get("regularMarketPreviousClose")
                        change_pct = None
                        if price is not None and prev_close is not None:
                            change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else None

                        # success
                        try:
                            observability.track_metric("market_yfinance_attempts", attempt, {"ticker": sym})
                        except Exception:
                            pass

                        return sym.upper(), {
                            "ticker": sym.upper(),
                            "price": price,
                            "currency": currency,
                            "change_pct": round(change_pct, 2) if change_pct is not None else None,
                            "timestamp": info.get("regularMarketTime"),
                            "source": "yfinance"
                        }
                    except Exception as e:
                        logger.warning(f"Attempt {attempt} failed for {sym}: {e}")
                        # If not last attempt, backoff a small amount and retry
                        if attempt < max_attempts:
                            backoff = 0.05 * (2 ** (attempt - 1))
                            time.sleep(backoff)
                            continue
                        # final failure
                        logger.error(f"Error fetching quote for {sym}: {e}")
                        try:
                            observability.track_metric("market_yfinance_attempts", attempt, {"ticker": sym, "failed": True})
                        except Exception:
                            pass
                        return sym.upper(), {
                            "ticker": sym.upper(),
                            "price": None,
                            "currency": None,
                            "change_pct": None,
                            "error": str(e),
                            "source": "yfinance"
                        }

            with ThreadPoolExecutor(max_workers=max_workers) as exe:
                futures = {exe.submit(fetch_one, t): t for t in tickers}
                for fut in as_completed(futures):
                    k, v = fut.result()
                    results[k] = v

            return results
        finally:
            duration_ms = (time.time() - start) * 1000
            try:
                observability.track_metric("market_yfinance_batch_call_ms", duration_ms, {"count": len(tickers)})
                logger.info(f"yfinance batch fetch for {len(tickers)} tickers took {duration_ms:.2f}ms")
            except Exception:
                pass


class MarketMCPServer:
    """MCP Server for market data operations."""

    def __init__(self):
        self.tools = {
            "get_quote": GetQuoteTool(),
            "get_quotes": GetQuotesTool(),
        }

    def get_tools(self) -> list:
        """Return list of available tools."""
        return [tool.to_schema() for tool in self.tools.values()]

    def call_tool(self, name: str, arguments: dict) -> Any:
        """Call a tool by name with arguments."""
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        
        tool = self.tools[name]
        return tool.execute(**arguments)


# Singleton server instance
_server: MarketMCPServer | None = None


def get_server() -> MarketMCPServer:
    """Get or create the market MCP server."""
    global _server
    if _server is None:
        _server = MarketMCPServer()
    return _server
