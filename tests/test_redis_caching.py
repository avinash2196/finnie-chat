"""
Tests for Redis + In-Memory Caching Layer

Covers:
- Market quote caching (app/mcp/market.py)
- News article caching (app/mcp/news.py)
- Cache serialization/deserialization
- TTL behavior
- Cache miss and fallback scenarios
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from app.mcp.market import MarketClient, MarketQuote
from app.mcp.news import NewsClient, NewsArticle


class TestMarketClientCaching:
    """Test Market Client caching behavior"""

    def test_market_client_initialization(self):
        """Test MarketClient initializes with caching"""
        client = MarketClient()
        assert client is not None
        assert hasattr(client, '_cache')
        assert isinstance(client._cache, dict)

    def test_market_client_freshness_check(self):
        """Test TTL freshness check"""
        client = MarketClient(ttl_seconds=10)
        
        # Add item to cache
        key = "GOOG"
        client._cache[key] = {"ts": time.time(), "quote": MagicMock()}
        
        # Should be fresh
        assert client._is_fresh(key) is True
        
        # Manually age it
        client._cache[key]["ts"] = time.time() - 15
        
        # Should be stale now
        assert client._is_fresh(key) is False

    def test_market_client_serialize_quote(self):
        """Test MarketQuote serialization"""
        client = MarketClient()
        quote = MarketQuote(
            ticker="TSLA",
            price=250.5,
            currency="USD",
            change_pct=3.2,
            timestamp=1700000000.0
        )
        
        serialized = client._serialize_quote(quote)
        assert isinstance(serialized, str)
        assert "TSLA" in serialized
        assert "250.5" in serialized
        
        # Verify it's valid JSON
        data = json.loads(serialized)
        assert data["ticker"] == "TSLA"
        assert data["price"] == 250.5

    def test_market_client_deserialize_quote(self):
        """Test MarketQuote deserialization"""
        client = MarketClient()
        quote = MarketQuote(
            ticker="NVDA",
            price=500.0,
            currency="USD",
            change_pct=5.0,
            timestamp=1700000000.0
        )
        
        serialized = client._serialize_quote(quote)
        deserialized = client._deserialize_quote(serialized)
        
        assert deserialized is not None
        assert deserialized.ticker == quote.ticker
        assert deserialized.price == quote.price
        assert deserialized.currency == quote.currency

    def test_market_client_deserialize_invalid_json(self):
        """Test deserialize handles invalid JSON"""
        client = MarketClient()
        deserialized = client._deserialize_quote("invalid json")
        assert deserialized is None

    def test_market_client_deserialize_null_price_with_error(self):
        """Test deserialize returns None for null price with error"""
        client = MarketClient()
        payload = json.dumps({
            "ticker": "INVALID",
            "price": None,
            "currency": "USD",
            "change_pct": 0,
            "timestamp": time.time(),
            "error": "Ticker not found"
        })
        
        deserialized = client._deserialize_quote(payload)
        assert deserialized is None


class TestNewsClientCaching:
    """Test News Client caching behavior"""

    def test_news_client_initialization(self):
        """Test NewsClient initializes with caching"""
        client = NewsClient()
        assert client is not None
        assert hasattr(client, '_cache')
        assert isinstance(client._cache, dict)

    def test_news_client_freshness_check(self):
        """Test news cache TTL freshness"""
        client = NewsClient(ttl_seconds=5)
        
        # Create a key similar to what the client creates
        key = "GOOG:3"
        client._cache[key] = {"ts": time.time(), "data": []}
        
        # Should be fresh immediately
        assert client._is_fresh(key) is True
        
        # Age it beyond TTL
        client._cache[key]["ts"] = time.time() - 10
        assert client._is_fresh(key) is False

    def test_news_client_article_serialization(self):
        """Test NewsArticle serialization"""
        client = NewsClient()
        article = NewsArticle(
            title="Market Update",
            url="https://example.com/news",
            summary="Test summary",
            time_published="2024-01-15T10:00:00Z",
            source="Reuters",
            tickers=["AAPL"]
        )
        
        articles = [article]
        serialized = client._serialize(articles)
        
        assert isinstance(serialized, str)
        assert "Market Update" in serialized
        assert "Reuters" in serialized

    def test_news_client_article_deserialization(self):
        """Test NewsArticle deserialization"""
        client = NewsClient()
        article = NewsArticle(
            title="Tech News",
            url="https://example.com/tech",
            summary="Technology update",
            time_published="2024-01-15T11:00:00Z",
            source="TechNews",
            tickers=["TSLA", "NVDA"]
        )
        
        articles = [article]
        serialized = client._serialize(articles)
        deserialized = client._deserialize(serialized)
        
        assert len(deserialized) == 1
        assert deserialized[0].title == article.title
        assert deserialized[0].source == article.source
        assert "TSLA" in deserialized[0].tickers

    def test_news_client_invalid_deserialization(self):
        """Test deserialization handles invalid data"""
        client = NewsClient()
        deserialized = client._deserialize("invalid json")
        assert isinstance(deserialized, list)
        # Should return empty list on error
        assert len(deserialized) == 0


class TestCachingWithRedis:
    """Test Redis caching fallback behavior"""

    def test_redis_initialization_failure_fallback(self):
        """Test graceful fallback when Redis unavailable"""
        # This should not raise, just use in-memory cache
        with patch.dict('os.environ', {'REDIS_URL': 'redis://invalid:9999'}):
            client = MarketClient()
            # Should still initialize with None redis
            assert client._redis is None
            # In-memory cache should still work
            assert isinstance(client._cache, dict)

    def test_caching_works_without_redis(self):
        """Test caching works with in-memory only"""
        import os
        # Ensure Redis URL not set
        redis_url = os.getenv('REDIS_URL')
        try:
            if 'REDIS_URL' in os.environ:
                del os.environ['REDIS_URL']
            
            client = MarketClient()
            assert client._redis is None
            
            # Cache should still work - use ticker directly as key
            key = "TEST"
            quote = MarketQuote(
                ticker=key,
                price=100.0,
                currency="USD",
                change_pct=1.0,
                timestamp=time.time()
            )
            client._cache[key] = {"ts": time.time(), "quote": quote}
            assert client._is_fresh(key) is True
        finally:
            if redis_url:
                os.environ['REDIS_URL'] = redis_url


class TestCachingIntegration:
    """Integration tests for caching behavior"""

    def test_market_and_news_independent_caches(self):
        """Test that market and news caches are independent"""
        market_client = MarketClient()
        news_client = NewsClient()
        
        # They should have separate caches
        market_key = "AAPL"  # Direct key, not via _key method
        news_key = "test-news"
        
        # Add to each cache
        market_quote = MarketQuote(
            ticker=market_key,
            price=150.0,
            currency="USD",
            change_pct=2.0,
            timestamp=time.time()
        )
        market_client._cache[market_key] = {"data": market_quote}
        news_client._cache[news_key] = {"data": "news"}
        
        # Verify they're independent
        assert market_client._cache != news_client._cache

    def test_cache_ttl_configured_per_client(self):
        """Test that TTL can be configured per client"""
        market_short = MarketClient(ttl_seconds=2)
        market_long = MarketClient(ttl_seconds=30)
        
        assert market_short._ttl == 2
        assert market_long._ttl == 30

    def test_news_redis_ttl_separate_from_memory_ttl(self):
        """Test that Redis and memory TTLs can differ"""
        client = NewsClient(ttl_seconds=5, redis_ttl_seconds=300)
        
        assert client._ttl == 5
        assert client._redis_ttl == 300


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
