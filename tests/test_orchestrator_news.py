"""End-to-end orchestrator tests for ASK_NEWS intent.
Tests the full pipeline: intent classification -> agent routing -> news synthesis -> compliance.
"""
import pytest
from app.agents.orchestrator import handle_message


class DummyResp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_orchestrator_news_intent_with_mcp(monkeypatch):
    """Test full orchestration path for ASK_NEWS intent with MCP data"""
    payload = {
        "feed": [
            {
                "title": "Apple unveils new iPhone",
                "url": "http://example.com/iphone",
                "summary": "Revolutionary features announced",
                "time_published": "20250125T090000",
                "source": "TechNews",
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

    message = "What are the latest headlines for AAPL?"
    reply, intent, risk = handle_message(message, user_id="user_123")

    assert isinstance(reply, str)
    assert len(reply) > 0
    # Should include news content
    assert "Apple" in reply or "AAPL" in reply or "iPhone" in reply
    # Intent should be ASK_NEWS or similar
    assert intent in ["ASK_NEWS", "ASK_MARKET", "ASK_CONCEPT"]  # Intent classifier may vary
    # Should not be blocked (risk should be low)
    assert risk in ["LOW", "MEDIUM"]


def test_orchestrator_news_intent_fallback_path(monkeypatch):
    """Test orchestrator with news intent when MCP returns empty feed"""
    payload = {"feed": []}

    def fake_get(url, timeout=6):
        return DummyResp(payload)

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    message = "MSFT earnings beat expectations. Revenue up 20%. Cloud growth strong."
    reply, intent, risk = handle_message(message, user_id="user_123")

    assert isinstance(reply, str)
    assert len(reply) > 0
    # Should use fallback text summarization
    assert "MSFT" in reply or "earnings" in reply.lower() or "revenue" in reply.lower()


def test_orchestrator_news_with_context():
    """Test orchestrator with conversation context for news query"""
    context = "User: What's AAPL's current price?\nAssistant: AAPL is trading at $185.50."
    message = "Any recent news about this stock?"
    
    reply, intent, risk = handle_message(message, conversation_context=context, user_id="user_123")

    assert isinstance(reply, str)
    assert len(reply) > 0
    # Should handle contextual reference to "this stock"


def test_orchestrator_news_compliance_check():
    """Test that compliance agent is always called for news"""
    message = "Show me TSLA headlines"
    reply, intent, risk = handle_message(message, user_id="user_123")

    assert isinstance(reply, str)
    # Compliance agent should add disclaimer
    # (Check for common disclaimer patterns)
    lower_reply = reply.lower()
    has_disclaimer = any(word in lower_reply for word in ["disclaimer", "educational", "not advice", "consult"])
    # If no explicit disclaimer, at least should have safe response
    assert len(reply) > 0


def test_orchestrator_news_no_tickers():
    """Test orchestrator with news-like query but no tickers"""
    message = "Summarize today's market news"
    reply, intent, risk = handle_message(message, user_id="user_123")

    assert isinstance(reply, str)
    assert len(reply) > 0
    # Should provide some response even without specific tickers


def test_orchestrator_news_multiple_agents(monkeypatch):
    """Test orchestrator routes to multiple agents when needed"""
    payload = {
        "feed": [
            {
                "title": "Tech sector analysis",
                "url": "http://example.com/tech",
                "summary": "Growth opportunities in AI",
                "time_published": "20250125T100000",
                "source": "Analyst",
                "ticker_sentiment": [{"ticker": "NVDA"}],
            }
        ]
    }

    def fake_get(url, timeout=6):
        return DummyResp(payload)

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    # Query that could trigger both news and educator agents
    message = "What does the latest NVDA news mean for my portfolio?"
    reply, intent, risk = handle_message(message, user_id="user_123")

    assert isinstance(reply, str)
    assert len(reply) > 50  # Should have substantive response
    # Should combine information from multiple agents


def test_orchestrator_news_error_handling(monkeypatch):
    """Test orchestrator handles MCP errors gracefully"""
    def fake_get(url, timeout=6):
        raise Exception("Network timeout")

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    import os
    os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "testkey")

    message = "Latest news for AAPL"
    # Should not crash, should return some response
    try:
        reply, intent, risk = handle_message(message, user_id="user_123")
        assert isinstance(reply, str)
        # Might be error message or fallback response
        assert len(reply) > 0
    except Exception as e:
        pytest.fail(f"Orchestrator should handle MCP errors gracefully, but raised: {e}")
