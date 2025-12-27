"""
MCP Server for financial news via Alpha Vantage NEWS_SENTIMENT.
Provides a tool to fetch recent news for tickers with simple normalization.
"""
import os
import time
import logging
from typing import Any, List, Dict, Optional
import requests

from app.observability import observability


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsTool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def to_schema(self) -> dict:
        raise NotImplementedError


class GetNewsTool(NewsTool):
    """Fetch recent news articles for given tickers using Alpha Vantage."""

    def __init__(self):
        super().__init__(
            name="get_news",
            description="Fetch recent news articles for tickers via Alpha Vantage NEWS_SENTIMENT"
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
                        "description": "List of ticker symbols (e.g., AAPL, MSFT)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of articles to return",
                        "default": 5
                    }
                },
                "required": ["tickers"]
            }
        }

    def execute(self, tickers: List[str], limit: int = 5) -> Dict[str, Any]:
        start = time.time()
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        symbols = ",".join([t.upper() for t in tickers])

        logger.info(f"[NEWS_MCP] Fetching news for tickers={tickers}, limit={limit}")

        if not api_key:
            logger.warning("[NEWS_MCP] Missing ALPHA_VANTAGE_API_KEY")
            return {"error": "Missing ALPHA_VANTAGE_API_KEY", "articles": []}
        if not symbols:
            logger.warning("[NEWS_MCP] No tickers provided")
            return {"error": "No tickers provided", "articles": []}

        url = (
            "https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
            f"&tickers={symbols}&sort=LATEST&apikey={api_key}"
        )
        logger.debug(f"[NEWS_MCP] Alpha Vantage URL: {url[:80]}...")
        try:
            resp = requests.get(url, timeout=6)
            resp.raise_for_status()
            data = resp.json() or {}
            feed = data.get("feed", [])

            logger.info(f"[NEWS_MCP] Alpha Vantage returned {len(feed)} items in feed")

            articles = []
            for item in feed[: max(1, limit)]:
                # Normalize fields safely
                tickers_in_article = []
                for ts in item.get("ticker_sentiment", []) or []:
                    sym = ts.get("ticker")
                    if sym:
                        tickers_in_article.append(sym.upper())

                articles.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "summary": item.get("summary") or item.get("overall_sentiment_score"),
                    "time_published": item.get("time_published"),
                    "source": item.get("source"),
                    "tickers": list(dict.fromkeys(tickers_in_article))
                })

            logger.info(f"[NEWS_MCP] Normalized {len(articles)} articles for response")
            return {"error": None, "articles": articles, "source": "alphavantage"}
        except Exception as e:
            logger.error(f"Alpha Vantage news error for {symbols}: {e}")
            return {"error": str(e), "articles": []}
        finally:
            duration_ms = (time.time() - start) * 1000
            try:
                observability.track_metric("news_alpha_vantage_call_ms", duration_ms, {"count": limit})
                logger.info(f"Alpha Vantage news for {symbols} took {duration_ms:.2f}ms")
            except Exception:
                pass


class GetGeneralNewsTool(NewsTool):
    """Fetch general market headlines without specific tickers."""

    def __init__(self):
        super().__init__(
            name="get_general_news",
            description="Fetch general market headlines and top financial news"
        )

    def to_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max number of articles to return",
                        "default": 5
                    }
                },
                "required": []
            }
        }

    def execute(self, limit: int = 5) -> Dict[str, Any]:
        start = time.time()
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

        logger.info(f"[NEWS_MCP] Fetching general market headlines, limit={limit}")

        if not api_key:
            logger.warning("[NEWS_MCP] Missing ALPHA_VANTAGE_API_KEY")
            return {"error": "Missing ALPHA_VANTAGE_API_KEY", "articles": []}

        # Use topics parameter for general market news
        url = (
            "https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
            f"&topics=financial_markets,technology&sort=LATEST&limit={limit}&apikey={api_key}"
        )
        logger.debug(f"[NEWS_MCP] Alpha Vantage general news URL: {url[:80]}...")
        try:
            resp = requests.get(url, timeout=6)
            resp.raise_for_status()
            data = resp.json() or {}
            feed = data.get("feed", [])

            logger.info(f"[NEWS_MCP] Alpha Vantage returned {len(feed)} general news items")

            articles = []
            for item in feed[: max(1, limit)]:
                tickers_in_article = []
                for ts in item.get("ticker_sentiment", []) or []:
                    sym = ts.get("ticker")
                    if sym:
                        tickers_in_article.append(sym.upper())

                articles.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "summary": item.get("summary") or item.get("overall_sentiment_score"),
                    "time_published": item.get("time_published"),
                    "source": item.get("source"),
                    "tickers": list(dict.fromkeys(tickers_in_article))
                })

            logger.info(f"[NEWS_MCP] Normalized {len(articles)} general articles for response")
            return {"error": None, "articles": articles, "source": "alphavantage"}
        except Exception as e:
            logger.error(f"Alpha Vantage general news error: {e}")
            return {"error": str(e), "articles": []}
        finally:
            duration_ms = (time.time() - start) * 1000
            try:
                observability.track_metric("news_alpha_vantage_general_call_ms", duration_ms, {"limit": limit})
                logger.info(f"Alpha Vantage general news took {duration_ms:.2f}ms")
            except Exception:
                pass


class NewsMCPServer:
    def __init__(self):
        self.tools = {
            "get_news": GetNewsTool(),
            "get_general_news": GetGeneralNewsTool(),
        }

    def get_tools(self) -> list:
        return [tool.to_schema() for tool in self.tools.values()]

    def call_tool(self, name: str, arguments: dict) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        tool = self.tools[name]
        return tool.execute(**arguments)


_server: Optional[NewsMCPServer] = None


def get_server() -> NewsMCPServer:
    global _server
    if _server is None:
        _server = NewsMCPServer()
    return _server
