"""Tests for Risk Profiler Agent."""

import pytest
from unittest.mock import Mock, patch
from app.agents.risk_profiler import calculate_portfolio_metrics, run


class TestCalculatePortfolioMetrics:
    """Test portfolio metrics calculation."""

    @patch('app.agents.risk_profiler.get_client')
    def test_portfolio_volatility(self, mock_get_client):
        """Test calculating portfolio volatility."""
        # Mock market client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock quotes
        mock_aapl = Mock(price=165.0)
        mock_msft = Mock(price=330.0)
        mock_client.get_quote.side_effect = [mock_aapl, mock_msft]
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 150},
            'MSFT': {'quantity': 5, 'purchase_price': 300}
        }
        
        metrics = calculate_portfolio_metrics(holdings)
        
        assert 'volatility' in metrics
        assert metrics['volatility'] >= 0
        assert isinstance(metrics['volatility'], (int, float))

    @patch('app.agents.risk_profiler.get_client')
    def test_sharpe_ratio_calculation(self, mock_get_client):
        """Test Sharpe ratio calculation."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_aapl = Mock(price=150.0)  # No change
        mock_client.get_quote.return_value = mock_aapl
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 150}
        }
        
        metrics = calculate_portfolio_metrics(holdings)
        
        assert 'sharpe_ratio' in metrics
        assert isinstance(metrics['sharpe_ratio'], (int, float))

    @patch('app.agents.risk_profiler.get_client')
    def test_avg_return_calculation(self, mock_get_client):
        """Test average return calculation."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # 10% gain on AAPL, 5% gain on MSFT
        mock_aapl = Mock(price=165.0)  # 150 -> 165
        mock_msft = Mock(price=315.0)  # 300 -> 315
        mock_client.get_quote.side_effect = [mock_aapl, mock_msft]
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 150},
            'MSFT': {'quantity': 5, 'purchase_price': 300}
        }
        
        metrics = calculate_portfolio_metrics(holdings)
        
        assert 'avg_return' in metrics
        assert metrics['avg_return'] > 0  # Should be positive

    @patch('app.agents.risk_profiler.get_client')
    def test_empty_holdings(self, mock_get_client):
        """Test with empty holdings."""
        holdings = {}
        metrics = calculate_portfolio_metrics(holdings)
        
        assert metrics.get('error') is not None

    @patch('app.agents.risk_profiler.get_client')
    def test_single_holding(self, mock_get_client):
        """Test with single holding."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_aapl = Mock(price=150.0)
        mock_client.get_quote.return_value = mock_aapl
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 150}}
        metrics = calculate_portfolio_metrics(holdings)
        
        assert 'volatility' in metrics
        # Single holding has 0 volatility
        assert metrics['volatility'] == 0


class TestRiskProfilerAgent:
    """Test Risk Profiler Agent main function."""

    def test_no_holdings(self):
        """Test with no holdings provided."""
        result = run("What is my risk?", holdings_dict=None)
        assert "No holdings" in result

    @patch('app.agents.risk_profiler.calculate_portfolio_metrics')
    @patch('app.agents.risk_profiler.call_llm')
    def test_run_with_holdings(self, mock_llm, mock_metrics):
        """Test running risk profiler with holdings."""
        mock_metrics.return_value = {
            'volatility': 15.5,
            'avg_return': 8.2,
            'sharpe_ratio': 0.53
        }
        mock_llm.return_value = "Your portfolio has moderate risk with good returns."
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 150},
            'MSFT': {'quantity': 5, 'purchase_price': 300}
        }
        
        result = run("What is my portfolio risk?", holdings_dict=holdings)
        
        assert isinstance(result, str)
        assert len(result) > 0
        mock_llm.assert_called_once()

    @patch('app.agents.risk_profiler.calculate_portfolio_metrics')
    def test_metrics_error_handling(self, mock_metrics):
        """Test error handling when metrics fail."""
        mock_metrics.return_value = {
            'error': 'Could not fetch price for INVALID'
        }
        
        holdings = {'INVALID': {'quantity': 10, 'purchase_price': 150}}
        result = run("What is my risk?", holdings_dict=holdings)
        
        assert "Error analyzing portfolio" in result

    @patch('app.agents.risk_profiler.calculate_portfolio_metrics')
    @patch('app.agents.risk_profiler.call_llm')
    def test_llm_error_handling(self, mock_llm, mock_metrics):
        """Test error handling when LLM fails."""
        mock_metrics.return_value = {
            'volatility': 15.5,
            'avg_return': 8.2,
            'sharpe_ratio': 0.53
        }
        mock_llm.side_effect = Exception("LLM service unavailable")
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 150}}
        result = run("What is my risk?", holdings_dict=holdings)
        
        # Should fallback to metrics display
        assert "Volatility" in result or "15.5" in result


class TestMetricsAccuracy:
    """Test accuracy of metric calculations."""

    @patch('app.agents.risk_profiler.get_client')
    def test_positive_returns(self, mock_get_client):
        """Test with positive returns."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # All stocks up 10%
        mock_client.get_quote.return_value = Mock(price=165.0)
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 150}}
        metrics = calculate_portfolio_metrics(holdings)
        
        assert metrics['avg_return'] == 10.0

    @patch('app.agents.risk_profiler.get_client')
    def test_negative_returns(self, mock_get_client):
        """Test with negative returns."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # All stocks down 5%
        mock_client.get_quote.return_value = Mock(price=142.5)
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 150}}
        metrics = calculate_portfolio_metrics(holdings)
        
        assert metrics['avg_return'] < 0
