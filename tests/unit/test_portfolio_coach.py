import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from app.agents import portfolio_coach


def test_analyze_allocation_handles_missing_price():
    holdings = {'FOO': {'quantity': 10, 'purchase_price': 1}}
    mock_client = MagicMock()
    mock_client.get_quote.return_value = SimpleNamespace(price=None)
    with patch('app.agents.portfolio_coach.get_client', return_value=mock_client):
        result = portfolio_coach.analyze_allocation(holdings)
        assert result['error'] is not None


def test_detect_concentration_edge_cases():
    # empty
    assert portfolio_coach.detect_concentration({}) == (False, 0, [])
    # single holding
    alloc = {'AAPL': {'percentage': 100}}
    assert portfolio_coach.detect_concentration(alloc)[0] is True
    # concentrated but below threshold
    alloc2 = {'A': {'percentage': 35}, 'B': {'percentage': 65}}
    is_conc, max_pct, ticks = portfolio_coach.detect_concentration(alloc2)
    assert isinstance(is_conc, bool)


def test_calculate_diversification_score_various_counts():
    assert portfolio_coach.calculate_diversification_score({}) == 0
    assert portfolio_coach.calculate_diversification_score({'A': {'percentage': 100}}) == 0
    val = portfolio_coach.calculate_diversification_score({'A': {'percentage': 50}, 'B': {'percentage': 50}})
    assert isinstance(val, float)


def test_run_handles_mcp_failure_and_llm_fallback():
    # Simulate get_portfolio_client raising
    with patch('app.agents.portfolio_coach.get_portfolio_client', side_effect=Exception('mcp fail')):
        out = portfolio_coach.run('Analyze', user_id='u1')
        assert 'Unable to fetch portfolio data' in out
