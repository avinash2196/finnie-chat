"""
Client for Alpha Vantage News MCP server, with short-TTL caching.
"""
import time
from dataclasses import dataclass
from typing import Optional, List, Dict

from app.mcp.news_server import get_server as get_news_server


@dataclass
class NewsArticle:
    title: Optional[str]
    url: Optional[str]
    summary: Optional[str]
    time_published: Optional[str]
    source: Optional[str]
    tickers: List[str]


class NewsClient:
    def __init__(self, ttl_seconds: int = 30):
        self._server = get_news_server()
        self._cache: Dict[str, Dict] = {}
        self._ttl = ttl_seconds

    def _key(self, tickers: List[str], limit: int) -> str:
        return f"{','.join(sorted([t.upper() for t in tickers]))}:{limit}"

    def _is_fresh(self, key: str) -> bool:
        entry = self._cache.get(key)
        return bool(entry and (time.time() - entry.get("ts", 0) < self._ttl))

    def get_news(self, tickers: List[str], limit: int = 5) -> List[NewsArticle]:
        import logging
        logger = logging.getLogger(__name__)
        
        if not tickers:
            logger.warning("[NEWS_CLIENT] get_news called with empty tickers")
            return []
        key = self._key(tickers, limit)
        if self._is_fresh(key):
            logger.debug(f"[NEWS_CLIENT] Cache HIT for {tickers[:3]}...")
            return self._cache[key]["articles"]

        logger.info(f"[NEWS_CLIENT] Cache MISS, calling MCP for tickers={tickers}")
        raw = self._server.call_tool("get_news", {"tickers": tickers, "limit": limit})
        logger.info(f"[NEWS_CLIENT] MCP returned: error={raw.get('error')}, article_count={len(raw.get('articles', []))}")
        
        articles: List[NewsArticle] = []
        for a in (raw.get("articles") or []):
            articles.append(NewsArticle(
                title=a.get("title"),
                url=a.get("url"),
                summary=a.get("summary"),
                time_published=a.get("time_published"),
                source=a.get("source"),
                tickers=a.get("tickers") or []
            ))
        self._cache[key] = {"ts": time.time(), "articles": articles}
        return articles

    def get_general_news(self, limit: int = 5) -> List[NewsArticle]:
        import logging
        logger = logging.getLogger(__name__)
        
        key = f"general:{limit}"
        if self._is_fresh(key):
            logger.debug(f"[NEWS_CLIENT] Cache HIT for general news")
            return self._cache[key]["articles"]

        logger.info(f"[NEWS_CLIENT] Cache MISS, calling MCP for general news")
        raw = self._server.call_tool("get_general_news", {"limit": limit})
        logger.info(f"[NEWS_CLIENT] MCP returned: error={raw.get('error')}, article_count={len(raw.get('articles', []))}")
        
        articles: List[NewsArticle] = []
        for a in (raw.get("articles") or []):
            articles.append(NewsArticle(
                title=a.get("title"),
                url=a.get("url"),
                summary=a.get("summary"),
                time_published=a.get("time_published"),
                source=a.get("source"),
                tickers=a.get("tickers") or []
            ))
        self._cache[key] = {"ts": time.time(), "articles": articles}
        return articles


_client: Optional[NewsClient] = None


def get_client() -> NewsClient:
    global _client
    if _client is None:
        _client = NewsClient()
    return _client
