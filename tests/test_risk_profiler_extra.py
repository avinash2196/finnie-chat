"""Extra tests for Risk Profiler to cover missed branches."""

from unittest.mock import MagicMock, patch
from app.agents.risk_profiler import calculate_portfolio_metrics, run


@patch('app.agents.risk_profiler.get_client')
def test_calculate_metrics_missing_quote_error(mock_get_client):
    """If any quote has no price, returns early with error."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    # First ticker returns None price to trigger early error path
    mock_client.get_quote.side_effect = [MagicMock(price=None), MagicMock(price=200.0)]

    holdings = {
        'AAPL': {'quantity': 10, 'purchase_price': 150},
        'MSFT': {'quantity': 5, 'purchase_price': 300}
    }
    metrics = calculate_portfolio_metrics(holdings)
    assert metrics.get('error') is not None
    assert metrics['volatility'] is None


def test_run_with_empty_holdings_dict():
    """Providing an empty holdings dict should return no-holdings message."""
    result = run("Assess my risk", holdings_dict={})
    assert "No holdings" in result
