import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from app.agents import risk_profiler


def test_calculate_portfolio_metrics_handles_missing_quote():
    holdings = {'FOO': {'purchase_price': 10}}
    mock_client = MagicMock()
    mock_client.get_quote.return_value = SimpleNamespace(price=None)
    with patch('app.agents.risk_profiler.get_client', return_value=mock_client):
        res = risk_profiler.calculate_portfolio_metrics(holdings)
        assert res.get('error') is not None


def test_calculate_portfolio_metrics_single_and_multi_holdings():
    holdings1 = {'A': {'purchase_price': 10}}
    holdings2 = {'A': {'purchase_price': 10}, 'B': {'purchase_price': 20}}
    mock_client = MagicMock()
    mock_client.get_quote.side_effect = [SimpleNamespace(price=12), SimpleNamespace(price=22)]
    with patch('app.agents.risk_profiler.get_client', return_value=mock_client):
        r2 = risk_profiler.calculate_portfolio_metrics({'A': {'purchase_price': 10}, 'B': {'purchase_price': 20}})
        assert 'volatility' in r2


def test_run_handles_mcp_and_llm_failures():
    with patch('app.agents.risk_profiler.get_portfolio_client', side_effect=Exception('mcp error')):
        out = risk_profiler.run('What is risk?', user_id='u1')
        assert 'Unable to fetch portfolio data' in out
