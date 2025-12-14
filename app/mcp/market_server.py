"""
MCP Server for market data operations.
Implements tools for fetching stock quotes, market trends, and portfolio data.
"""

import json
import logging
from typing import Any
import yfinance as yf

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
        try:
            t = yf.Ticker(ticker.upper())
            info = t.info or {}
            price = info.get("regularMarketPrice")
            currency = info.get("currency") or info.get("financialCurrency") or "USD"
            prev_close = info.get("regularMarketPreviousClose")
            
            change_pct = None
            if price is not None and prev_close is not None:
                change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else None

            return {
                "ticker": ticker.upper(),
                "price": price,
                "currency": currency,
                "change_pct": round(change_pct, 2) if change_pct is not None else None,
                "timestamp": info.get("regularMarketTime"),
                "source": "yfinance"
            }
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


class MarketMCPServer:
    """MCP Server for market data operations."""

    def __init__(self):
        self.tools = {
            "get_quote": GetQuoteTool(),
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
