"""
Client for Alpha Vantage News MCP server, with short-TTL caching.
Adds optional Redis cache with in-memory fallback.
"""
import os
import json
import time
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict

from app.mcp.news_server import get_server as get_news_server

try:  # Redis is optional
    import redis  # type: ignore
except Exception:
    redis = None


@dataclass
class NewsArticle:
    title: Optional[str]
    url: Optional[str]
    summary: Optional[str]
    time_published: Optional[str]
    source: Optional[str]
    tickers: List[str]


class NewsClient:
    def __init__(self, ttl_seconds: int = 5, redis_ttl_seconds: int = 5):
        self._server = get_news_server()
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

    def _key(self, tickers: List[str], limit: int) -> str:
        return f"{','.join(sorted([t.upper() for t in tickers]))}:{limit}"

    def _is_fresh(self, key: str) -> bool:
        entry = self._cache.get(key)
        return bool(entry and (time.time() - entry.get("ts", 0) < self._ttl))

    def _serialize(self, articles: List[NewsArticle]) -> str:
        return json.dumps([
            {
                "title": a.title,
                "url": a.url,
                "summary": a.summary,
                "time_published": a.time_published,
                "source": a.source,
                "tickers": a.tickers,
            }
            for a in articles
        ])

    def _deserialize(self, payload: str) -> List[NewsArticle]:
        try:
            raw = json.loads(payload)
            return [
                NewsArticle(
                    title=item.get("title"),
                    url=item.get("url"),
                    summary=item.get("summary"),
                    time_published=item.get("time_published"),
                    source=item.get("source"),
                    tickers=item.get("tickers") or [],
                )
                for item in raw
            ]
        except Exception:
            return []

    def get_news(self, tickers: List[str], limit: int = 5) -> List[NewsArticle]:
        import logging
        logger = logging.getLogger(__name__)
        
        if not tickers:
            logger.warning("[NEWS_CLIENT] get_news called with empty tickers")
            return []
        key = self._key(tickers, limit)

        if self._is_fresh(key):
            logger.debug(f"[NEWS_CLIENT] Cache HIT (memory) for {tickers[:3]}...")
            return self._cache[key]["articles"]

        if self._redis:
            try:
                cached = self._redis.get(f"news:{key}")
                if cached:
                    articles = self._deserialize(cached.decode("utf-8"))
                    if articles:
                        logger.debug(f"[NEWS_CLIENT] Cache HIT (redis) for {tickers[:3]}...")
                        # refresh in-memory cache
                        self._cache[key] = {"ts": time.time(), "articles": articles}
                        return articles
            except Exception:
                pass

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
        if articles:
            self._cache[key] = {"ts": time.time(), "articles": articles}
            if self._redis:
                try:
                    self._redis.setex(f"news:{key}", self._redis_ttl, self._serialize(articles))
                except Exception:
                    pass
        return articles

    def get_general_news(self, limit: int = 5) -> List[NewsArticle]:
        import logging
        logger = logging.getLogger(__name__)
        
        key = f"general:{limit}"
        if self._is_fresh(key):
            logger.debug(f"[NEWS_CLIENT] Cache HIT (memory) for general news")
            return self._cache[key]["articles"]

        if self._redis:
            try:
                cached = self._redis.get(f"news:{key}")
                if cached:
                    articles = self._deserialize(cached.decode("utf-8"))
                    if articles:
                        logger.debug(f"[NEWS_CLIENT] Cache HIT (redis) for general news")
                        self._cache[key] = {"ts": time.time(), "articles": articles}
                        return articles
            except Exception:
                pass

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
        if articles:
            self._cache[key] = {"ts": time.time(), "articles": articles}
            if self._redis:
                try:
                    self._redis.setex(f"news:{key}", self._redis_ttl, self._serialize(articles))
                except Exception:
                    pass
        return articles


_client: Optional[NewsClient] = None


def get_client() -> NewsClient:
    global _client
    if _client is None:
        _client = NewsClient()
    return _client
