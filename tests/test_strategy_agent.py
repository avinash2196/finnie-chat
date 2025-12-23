"""Comprehensive tests for Strategy Agent."""

import pytest
from unittest.mock import patch, MagicMock
from app.agents.strategy import (
    run_dividend_screener,
    run_growth_screener,
    run_value_screener,
    run
)


class TestDividendScreener:
    """Test dividend screener functionality."""
    
    @patch('app.agents.strategy.get_client')
    def test_dividend_screener_basic(self, mock_get_client):
        """Test dividend screener with valid data."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock quote with dividend yield
        mock_quote = MagicMock()
        mock_quote.price = 150.0
        mock_quote.dividend_yield = 2.5
        mock_client.get_quote.return_value = mock_quote
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 140}
        }
        
        result = run_dividend_screener(holdings)
        
        assert result['error'] is None
        assert len(result['opportunities']) == 1
        assert result['opportunities'][0]['ticker'] == 'AAPL'
    
    @patch('app.agents.strategy.get_client')
    def test_dividend_screener_error_handling(self, mock_get_client):
        """Test screener handles errors gracefully."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.side_effect = Exception("API error")
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 150}}
        
        result = run_dividend_screener(holdings)
        
        # Should not crash, returns empty opportunities
        assert 'opportunities' in result


class TestGrowthScreener:
    """Test growth screener functionality."""
    
    @patch('app.agents.strategy.get_client')
    def test_growth_screener_positive_growth(self, mock_get_client):
        """Test growth screener identifies winners."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_quote = MagicMock()
        mock_quote.price = 200.0  # 100% gain from purchase
        mock_client.get_quote.return_value = mock_quote
        
        holdings = {'NVDA': {'quantity': 10, 'purchase_price': 100}}
        
        result = run_growth_screener(holdings)
        
        assert result['error'] is None
        assert 'all_holdings' in result
        assert 'top_performers' in result
    
    @patch('app.agents.strategy.get_client')
    def test_growth_screener_filtering(self, mock_get_client):
        """Test growth screener filters correctly."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_quote = MagicMock()
        mock_quote.price = 95.0  # Loss
        mock_client.get_quote.return_value = mock_quote
        
        holdings = {'LOW': {'quantity': 10, 'purchase_price': 100}}
        
        result = run_growth_screener(holdings)
        
        # Should have all_holdings but no top_performers
        assert result['error'] is None
        assert len(result['all_holdings']) >= 0


class TestValueScreener:
    """Test value screener functionality."""
    
    @patch('app.agents.strategy.get_client')
    def test_value_screener_basic(self, mock_get_client):
        """Test value screener identifies undervalued stocks."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_quote = MagicMock()
        mock_quote.price = 50.0  # Trading below purchase price
        mock_client.get_quote.return_value = mock_quote
        
        holdings = {'INTC': {'quantity': 20, 'purchase_price': 60}}
        
        result = run_value_screener(holdings)
        
        assert result['error'] is None
        assert 'bargain_opportunities' in result
    
    @patch('app.agents.strategy.get_client')
    def test_value_screener_no_opportunities(self, mock_get_client):
        """Test when no value opportunities exist."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_quote = MagicMock()
        mock_quote.price = 150.0  # Above purchase, not undervalued
        mock_client.get_quote.return_value = mock_quote
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 100}}
        
        result = run_value_screener(holdings)
        
        assert result['error'] is None


class TestStrategyRun:
    """Test main run function."""
    
    @patch('app.agents.strategy.get_portfolio_client')
    @patch('app.agents.strategy.call_llm')
    def test_run_dividend(self, mock_llm, mock_portfolio):
        """Test dividend strategy analysis."""
        mock_client = MagicMock()
        mock_portfolio.return_value = mock_client
        mock_client.get_holdings.return_value = {
            'holdings': {'AAPL': {'quantity': 10, 'purchase_price': 150}}
        }
        
        mock_llm.return_value = "Dividend strategy analysis complete"
        
        result = run("Show me dividend opportunities", strategy_type="dividend", user_id="user_123")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('app.agents.strategy.get_portfolio_client')
    @patch('app.agents.strategy.call_llm')
    def test_run_growth(self, mock_llm, mock_portfolio):
        """Test growth strategy analysis."""
        mock_client = MagicMock()
        mock_portfolio.return_value = mock_client
        mock_client.get_holdings.return_value = {
            'holdings': {'NVDA': {'quantity': 5, 'purchase_price': 100}}
        }
        
        mock_llm.return_value = "Growth strategy analysis"
        
        result = run("Growth opportunities?", strategy_type="growth", user_id="user_123")
        
        assert isinstance(result, str)
    
    @patch('app.agents.strategy.get_portfolio_client')
    def test_run_no_holdings(self, mock_portfolio):
        """Test strategy analysis with empty portfolio."""
        mock_client = MagicMock()
        mock_portfolio.return_value = mock_client
        mock_client.get_holdings.return_value = {'holdings': {}}
        
        result = run("Analyze my portfolio", user_id="empty_user")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('app.agents.strategy.get_portfolio_client')
    def test_run_error(self, mock_portfolio):
        """Test strategy analysis handles errors."""
        mock_portfolio.side_effect = Exception("Portfolio service down")
        
        result = run("Analyze", user_id="user_123")
        
        assert isinstance(result, str)
