import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from app.agents import market


def test_extract_ticker_llm_and_fallbacks():
    # LLM returns JSON
    with patch('app.agents.market.call_llm', return_value='{"ticker":"AAPL"}'):
        assert market.extract_ticker("What is AAPL doing?") == 'AAPL'

    # LLM fails -> heuristic fallback
    with patch('app.agents.market.call_llm', side_effect=Exception("fail")):
        assert market.extract_ticker("How is Apple stock?") == 'AAPL'


def test_run_with_no_ticker_returns_error_message():
    out = market.run("Tell me about the economy")
    assert "couldn't identify" in out


def test_run_handles_missing_quote_price():
    mock_client = MagicMock()
    mock_client.get_quote.return_value = SimpleNamespace(price=None, error='not found', ticker='FOO')
    with patch.object(market, '_client', mock_client):
        out = market.run("What's FOO doing?")
        assert "Market data unavailable for" in out


def test_get_market_data_returns_none_on_missing_price():
    mock_client = MagicMock()
    mock_client.get_quote.return_value = SimpleNamespace(price=None, error='err')
    with patch.object(market, '_client', mock_client):
        assert market.get_market_data('FOO') is None
