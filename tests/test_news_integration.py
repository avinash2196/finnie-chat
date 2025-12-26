"""Integration tests for News Synthesizer Agent with MCP.
Tests the full path: agent -> client -> server -> normalization.
"""
import pytest
from app.agents.news_synthesizer import run as news_synthesizer_run


class DummyResp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_news_agent_with_mcp_success(monkeypatch):
    """Test news agent successfully calling MCP and building summary"""
    payload = {
        "feed": [
            {
                "title": "Apple announces new AI features",
                "url": "http://example.com/apple-ai",
                "summary": "Revolutionary AI integration across devices",
                "time_published": "20250125T100000",
                "source": "TechCrunch",
                "ticker_sentiment": [{"ticker": "AAPL"}],
            },
            {
                "title": "Apple stock surges on earnings",
                "url": "http://example.com/apple-earnings",
                "summary": "Better than expected quarterly results",
                "time_published": "20250125T093000",
                "source": "Bloomberg",
                "ticker_sentiment": [{"ticker": "AAPL"}],
            }
        ]
    }

    def fake_get(url, timeout=6):
        return DummyResp(payload)

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    message = "Show me latest headlines for AAPL"
    result = news_synthesizer_run(message)

    assert isinstance(result, str)
    assert "Apple" in result or "AAPL" in result
    assert "News Summary" in result
    assert "Citations" in result
    assert "AAPL" in result  # Ticker should be cited


def test_news_agent_with_mcp_empty_feed(monkeypatch):
    """Test news agent when MCP returns empty feed (falls back to text summarization)"""
    payload = {"feed": []}

    def fake_get(url, timeout=6):
        return DummyResp(payload)

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    # Message with ticker but will get empty feed
    message = "AAPL stock is up 5% today. Earnings beat expectations. Strong growth."
    result = news_synthesizer_run(message)

    assert isinstance(result, str)
    # Should fall back to summarizing provided text
    assert len(result) > 0
    assert "AAPL" in result or "Citations" in result


def test_news_agent_no_tickers_fallback():
    """Test news agent with no tickers detected (pure text fallback)"""
    message = "The market is doing well today. Many stocks are up."
    result = news_synthesizer_run(message)

    assert isinstance(result, str)
    assert len(result) > 0
    # Should use fallback text summarization
    assert "market" in result.lower() or "stocks" in result.lower()


def test_news_agent_compliance_gate():
    """Test news agent blocks buy/sell recommendations"""
    message = "What should I buy today? Give me stock picks."
    result = news_synthesizer_run(message)

    assert isinstance(result, str)
    assert "COMPLIANCE GATE" in result
    assert "cannot recommend" in result.lower()


def test_news_agent_with_multiple_tickers(monkeypatch):
    """Test news agent with multiple tickers"""
    payload = {
        "feed": [
            {
                "title": "Tech stocks rally amid AI boom",
                "url": "http://example.com/tech-rally",
                "summary": "AAPL, MSFT, GOOGL lead gains",
                "time_published": "20250125T110000",
                "source": "Reuters",
                "ticker_sentiment": [
                    {"ticker": "AAPL"},
                    {"ticker": "MSFT"},
                    {"ticker": "GOOGL"}
                ],
            }
        ]
    }

    def fake_get(url, timeout=6):
        return DummyResp(payload)

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    message = "Latest news on AAPL MSFT GOOGL"
    result = news_synthesizer_run(message)

    assert isinstance(result, str)
    # Should cite multiple tickers
    citation_section = result.split("Citations")[1] if "Citations" in result else result
    assert "AAPL" in citation_section or "MSFT" in citation_section or "GOOGL" in citation_section


def test_news_agent_mcp_api_error(monkeypatch):
    """Test news agent handles MCP API errors gracefully"""
    def fake_get(url, timeout=6):
        raise Exception("API rate limit exceeded")

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    # Should fall back to text summarization without crashing
    message = "AAPL announces new products. Stock rises 3%."
    result = news_synthesizer_run(message)

    assert isinstance(result, str)
    assert len(result) > 0


def test_news_agent_max_sentences_parameter(monkeypatch):
    """Test news agent respects max_sentences parameter"""
    payload = {
        "feed": [
            {"title": f"Article {i}", "url": f"http://ex.com/{i}",
             "summary": f"Summary {i}", "time_published": "20250125T120000",
             "source": "News", "ticker_sentiment": [{"ticker": "AAPL"}]}
            for i in range(10)
        ]
    }

    def fake_get(url, timeout=6):
        return DummyResp(payload)

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    message = "Show me AAPL news"
    result = news_synthesizer_run(message, max_sentences=2)

    assert isinstance(result, str)
    # Should have limited number of articles in summary
    bullet_count = result.count("- ")
    assert bullet_count <= 3  # max_sentences=2 might fetch 2-3 items


def test_news_agent_empty_message():
    """Test news agent with empty message"""
    result = news_synthesizer_run("")

    assert isinstance(result, str)
    assert "Please provide" in result or "news snippet" in result.lower()
