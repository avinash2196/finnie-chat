import types
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from app.agents import market as market_agent


def _mock_quote(price=150.0, change_pct=1.2, currency="USD", source="mock", error=None):
    return SimpleNamespace(
        ticker="AAPL",
        price=price,
        change_pct=change_pct,
        currency=currency,
        timestamp=1234567890.0,
        source=source,
        error=error,
    )


def test_extract_ticker_llm_success():
    with patch("app.agents.market.call_llm", return_value='{"ticker":"SPY"}'):
        assert market_agent.extract_ticker("How is the S&P doing?") == "SPY"


def test_extract_ticker_llm_failure_fallback_common():
    with patch("app.agents.market.call_llm", side_effect=Exception("LLM down")):
        assert market_agent.extract_ticker("How is Apple doing today?") == "AAPL"


def test_extract_ticker_heuristic_uppercase():
    with patch("app.agents.market.call_llm", side_effect=Exception("LLM down")):
        assert market_agent.extract_ticker("Is TSLA still rallying?") == "TSLA"


def test_get_market_data_success():
    with patch.object(market_agent, "_client") as mock_client:
        mock_client.get_quote.return_value = _mock_quote(price=123.45, change_pct=0.5)
        data = market_agent.get_market_data("AAPL")
        assert data["ticker"] == "AAPL"
        assert data["price"] == 123.45
        assert data["change_pct"] == 0.5
        assert "currency" in data


def test_get_market_data_no_price_returns_none():
    with patch.object(market_agent, "_client") as mock_client:
        mock_client.get_quote.return_value = _mock_quote(price=None, error="API Error")
        assert market_agent.get_market_data("AAPL") is None


def test_run_message_happy_path():
    with patch.object(market_agent, "_client") as mock_client, \
         patch("app.agents.market.extract_ticker", return_value="AAPL"):
        mock_client.get_quote.return_value = _mock_quote(price=200.0, change_pct=2.0)
        out = market_agent.run("What's Apple doing?")
        assert "AAPL is trading at" in out


def test_run_message_no_ticker():
    with patch("app.agents.market.extract_ticker", return_value=None):
        out = market_agent.run("Tell me about markets")
        assert "couldn't identify a stock ticker" in out.lower()
