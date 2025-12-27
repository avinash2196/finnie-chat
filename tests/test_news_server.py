"""Unit tests for Alpha Vantage News MCP server.
Uses monkeypatch to avoid external network calls.
"""
import pytest
from app.mcp.news_server import get_server


class DummyResp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")
        return None

    def json(self):
        return self._payload


def test_get_news_normalization(monkeypatch):
    """Test successful news fetch and normalization"""
    payload = {
        "feed": [
            {
                "title": "Apple launches new product",
                "url": "http://example.com/a",
                "summary": "New product overview",
                "time_published": "20250101T120000",
                "source": "ExampleNews",
                "ticker_sentiment": [{"ticker": "AAPL"}, {"ticker": "MSFT"}],
            }
        ]
    }

    def fake_get(url, timeout=6):
        return DummyResp(payload)

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    server = get_server()
    result = server.call_tool("get_news", {"tickers": ["AAPL"], "limit": 3})
    assert result.get("error") is None
    arts = result.get("articles")
    assert isinstance(arts, list)
    assert len(arts) == 1
    assert arts[0]["title"] == "Apple launches new product"
    assert "AAPL" in arts[0]["tickers"]
    assert arts[0]["source"] == "ExampleNews"


def test_get_news_missing_api_key(monkeypatch):
    """Test behavior when ALPHA_VANTAGE_API_KEY is missing"""
    import os
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)

    server = get_server()
    result = server.call_tool("get_news", {"tickers": ["AAPL"], "limit": 3})
    assert result.get("error") == "Missing ALPHA_VANTAGE_API_KEY"
    assert result.get("articles") == []


def test_get_news_empty_tickers():
    """Test behavior when no tickers provided"""
    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    server = get_server()
    result = server.call_tool("get_news", {"tickers": [], "limit": 3})
    assert result.get("error") == "No tickers provided"
    assert result.get("articles") == []


def test_get_news_api_error(monkeypatch):
    """Test behavior when Alpha Vantage API returns error"""
    def fake_get(url, timeout=6):
        return DummyResp({}, status_code=500)

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    server = get_server()
    result = server.call_tool("get_news", {"tickers": ["AAPL"], "limit": 3})
    assert result.get("error") is not None
    assert result.get("articles") == []


def test_get_news_empty_feed(monkeypatch):
    """Test behavior when API returns empty feed"""
    payload = {"feed": []}

    def fake_get(url, timeout=6):
        return DummyResp(payload)

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    server = get_server()
    result = server.call_tool("get_news", {"tickers": ["AAPL"], "limit": 3})
    assert result.get("error") is None
    assert result.get("articles") == []


def test_get_news_multiple_tickers(monkeypatch):
    """Test fetching news for multiple tickers"""
    payload = {
        "feed": [
            {
                "title": "Tech stocks rally",
                "url": "http://example.com/tech",
                "summary": "AAPL and MSFT surge",
                "time_published": "20250101T140000",
                "source": "TechNews",
                "ticker_sentiment": [{"ticker": "AAPL"}, {"ticker": "MSFT"}],
            },
            {
                "title": "Microsoft earnings beat",
                "url": "http://example.com/msft",
                "summary": "Strong cloud growth",
                "time_published": "20250101T130000",
                "source": "Finance",
                "ticker_sentiment": [{"ticker": "MSFT"}],
            }
        ]
    }

    def fake_get(url, timeout=6):
        return DummyResp(payload)

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    server = get_server()
    result = server.call_tool("get_news", {"tickers": ["AAPL", "MSFT"], "limit": 5})
    assert result.get("error") is None
    arts = result.get("articles")
    assert len(arts) == 2
    assert "MSFT" in arts[0]["tickers"]
    assert "MSFT" in arts[1]["tickers"]


def test_get_news_limit_respected(monkeypatch):
    """Test that limit parameter caps returned articles"""
    payload = {
        "feed": [
            {"title": f"Article {i}", "url": f"http://ex.com/{i}", "summary": f"Summary {i}",
             "time_published": "20250101T120000", "source": "News",
             "ticker_sentiment": [{"ticker": "AAPL"}]}
            for i in range(10)
        ]
    }

    def fake_get(url, timeout=6):
        return DummyResp(payload)

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    server = get_server()
    result = server.call_tool("get_news", {"tickers": ["AAPL"], "limit": 3})
    assert result.get("error") is None
    arts = result.get("articles")
    assert len(arts) == 3
