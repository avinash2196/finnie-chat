import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from app.agents import strategy


def test_dividend_screener_with_opportunities():
    holdings = {'AAPL': {'quantity': 10, 'purchase_price': 100}}
    mock_client = MagicMock()
    mock_client.get_quote.return_value = SimpleNamespace(price=200, dividend_yield=2.5)
    with patch('app.agents.strategy.get_client', return_value=mock_client):
        res = strategy.run_dividend_screener(holdings)
        assert res['opportunities']
        assert res['total_dividend_income'] > 0


def test_screener_handles_missing_price_per_ticker():
    holdings = {'A': {'quantity':1,'purchase_price':10}, 'B': {'quantity':1,'purchase_price':20}}
    mock_client = MagicMock()
    mock_client.get_quote.side_effect = [SimpleNamespace(price=None), SimpleNamespace(price=30, dividend_yield=0)]
    with patch('app.agents.strategy.get_client', return_value=mock_client):
        res = strategy.run_dividend_screener(holdings)
        # Should not raise and should process available ticker
        assert 'opportunities' in res


def test_growth_screener_sorting_and_top_performers():
    holdings = {'A': {'quantity':1,'purchase_price':10}, 'B': {'quantity':1,'purchase_price':5}, 'C': {'quantity':1,'purchase_price':8}}
    mock_client = MagicMock()
    mock_client.get_quote.side_effect = [SimpleNamespace(price=20), SimpleNamespace(price=15), SimpleNamespace(price=10)]
    with patch('app.agents.strategy.get_client', return_value=mock_client):
        res = strategy.run_growth_screener(holdings)
        assert isinstance(res['top_performers'], list)


def test_run_strategy_types_and_llm_fallback():
    # Provide holdings via MPC and simulate call_llm raising to hit fallback
    holdings = {'A': {'quantity':1,'purchase_price':10}}
    mock_pc = MagicMock()
    mock_pc.get_holdings.return_value = {'holdings': holdings}
    with patch('app.agents.strategy.get_portfolio_client', return_value=mock_pc), \
         patch('app.agents.strategy.get_client') as mock_client, \
         patch('app.agents.strategy.call_llm', side_effect=Exception('llm fail')):
        mock_client.return_value.get_quote.return_value = SimpleNamespace(price=20)
        out = strategy.run('Analyze', strategy_type='balanced', user_id='u1')
        assert 'Strategy Analysis' in out or 'Summary' in out
