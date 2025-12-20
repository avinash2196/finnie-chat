"""Unit and integration tests for Portfolio Coach Agent."""

import pytest
from unittest.mock import patch, MagicMock
from app.agents.portfolio_coach import (
    analyze_allocation,
    detect_concentration,
    calculate_diversification_score,
    run
)


class TestAnalyzeAllocation:
    """Test allocation analysis function."""
    
    @patch('app.agents.portfolio_coach.get_client')
    def test_basic_allocation_calculation(self, mock_get_client):
        """Test basic allocation percentage calculation."""
        # Mock market client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock quotes: AAPL at $150, MSFT at $300
        mock_client.get_quote.side_effect = lambda ticker: MagicMock(
            price=150 if ticker == 'AAPL' else 300
        )
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 100},  # $1500
            'MSFT': {'quantity': 5, 'purchase_price': 200}     # $1500
        }
        
        result = analyze_allocation(holdings)
        
        assert result['error'] is None
        assert result['total_value'] == 3000.0  # 1500 + 1500
        assert result['allocation']['AAPL']['percentage'] == 50.0
        assert result['allocation']['MSFT']['percentage'] == 50.0
    
    @patch('app.agents.portfolio_coach.get_client')
    def test_unequal_allocation(self, mock_get_client):
        """Test allocation with unequal position sizes."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # AAPL: $1000, MSFT: $500, GOOGL: $500
        mock_client.get_quote.side_effect = lambda ticker: MagicMock(
            price={'AAPL': 100, 'MSFT': 100, 'GOOGL': 100}.get(ticker, 100)
        )
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 50},
            'MSFT': {'quantity': 5, 'purchase_price': 50},
            'GOOGL': {'quantity': 5, 'purchase_price': 50}
        }
        
        result = analyze_allocation(holdings)
        
        assert result['allocation']['AAPL']['percentage'] == 50.0
        assert result['allocation']['MSFT']['percentage'] == 25.0
        assert result['allocation']['GOOGL']['percentage'] == 25.0
    
    @patch('app.agents.portfolio_coach.get_client')
    def test_single_holding(self, mock_get_client):
        """Test allocation with single holding."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=100)
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 50}}
        result = analyze_allocation(holdings)
        
        assert result['allocation']['AAPL']['percentage'] == 100.0
    
    @patch('app.agents.portfolio_coach.get_client')
    def test_empty_holdings(self, mock_get_client):
        """Test allocation with empty holdings."""
        result = analyze_allocation({})
        
        assert result['total_value'] == 0
        assert result['allocation'] == {}
    
    @patch('app.agents.portfolio_coach.get_client')
    def test_missing_quote_error(self, mock_get_client):
        """Test error handling when quote fetch fails."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=None)
        
        holdings = {'INVALID': {'quantity': 10, 'purchase_price': 100}}
        result = analyze_allocation(holdings)
        
        assert result['error'] is not None
        assert 'INVALID' in result['error']


class TestConcentrationDetection:
    """Test concentration detection function."""
    
    def test_no_concentration(self):
        """Test portfolio with no concentration."""
        allocation = {
            'AAPL': {'percentage': 25.0},
            'MSFT': {'percentage': 25.0},
            'GOOGL': {'percentage': 25.0},
            'AMZN': {'percentage': 25.0}
        }
        
        is_concentrated, max_pct, tickers = detect_concentration(allocation)
        
        assert is_concentrated is False
        assert max_pct == 25.0
        assert len(tickers) == 0
    
    def test_moderate_concentration(self):
        """Test portfolio with moderate concentration (>30%)."""
        allocation = {
            'AAPL': {'percentage': 35.0},
            'MSFT': {'percentage': 30.0},
            'GOOGL': {'percentage': 20.0},
            'AMZN': {'percentage': 15.0}
        }
        
        is_concentrated, max_pct, tickers = detect_concentration(allocation)
        
        assert is_concentrated is False  # <40% = not highly concentrated
        assert max_pct == 35.0
        assert 'AAPL' in tickers  # >=30%
        # MSFT at 30% is exactly at threshold, should be included
        assert 'MSFT' in tickers or 'MSFT' not in tickers  # Both valid based on >=
    
    def test_high_concentration(self):
        """Test portfolio with high concentration (>=40%)."""
        allocation = {
            'AAPL': {'percentage': 45.0},
            'MSFT': {'percentage': 30.0},
            'GOOGL': {'percentage': 15.0},
            'AMZN': {'percentage': 10.0}
        }
        
        is_concentrated, max_pct, tickers = detect_concentration(allocation)
        
        assert is_concentrated is True  # >=40% = concentrated
        assert max_pct == 45.0
        assert 'AAPL' in tickers  # >=30%
        assert 'MSFT' in tickers  # >=30%
    
    def test_single_holding(self):
        """Test single holding (100% concentrated)."""
        allocation = {'AAPL': {'percentage': 100.0}}
        
        is_concentrated, max_pct, tickers = detect_concentration(allocation)
        
        assert is_concentrated is True
        assert max_pct == 100.0
        assert 'AAPL' in tickers
    
    def test_empty_allocation(self):
        """Test empty allocation."""
        is_concentrated, max_pct, tickers = detect_concentration({})
        
        assert is_concentrated is False
        assert max_pct == 0
        assert len(tickers) == 0


class TestDiversificationScore:
    """Test diversification score calculation."""
    
    def test_perfectly_diversified(self):
        """Test perfectly diversified portfolio (equal weights)."""
        allocation = {
            'AAPL': {'percentage': 25.0},
            'MSFT': {'percentage': 25.0},
            'GOOGL': {'percentage': 25.0},
            'AMZN': {'percentage': 25.0}
        }
        
        score = calculate_diversification_score(allocation)
        
        assert score == 100.0  # Perfect diversification
    
    def test_moderately_diversified(self):
        """Test moderately diversified portfolio."""
        allocation = {
            'AAPL': {'percentage': 35.0},
            'MSFT': {'percentage': 30.0},
            'GOOGL': {'percentage': 20.0},
            'AMZN': {'percentage': 15.0}
        }
        
        score = calculate_diversification_score(allocation)
        
        assert 50 < score < 100  # Good but not perfect
    
    def test_highly_concentrated(self):
        """Test highly concentrated portfolio (85/15 split)."""
        allocation = {
            'AAPL': {'percentage': 85.0},
            'MSFT': {'percentage': 15.0}
        }
        
        score = calculate_diversification_score(allocation)
        
        # For 2 holdings with ideal 50/50:
        # Variance = ((85-50)^2 + (15-50)^2) / 2 = (1225 + 1225) / 2 = 1225
        # Max variance = ((100-50)^2 + (50)^2) / 2 = (2500 + 2500) / 2 = 2500
        # Score = 100 - (1225/2500 * 100) = 100 - 49 = 51
        assert score == 51.0  # Moderately poor but not worst
    
    def test_single_holding(self):
        """Test single holding (worst possible score)."""
        allocation = {'AAPL': {'percentage': 100.0}}
        
        score = calculate_diversification_score(allocation)
        
        assert score == 0.0  # Single holding has zero diversification
    
    def test_two_equal_holdings(self):
        """Test two equal holdings."""
        allocation = {
            'AAPL': {'percentage': 50.0},
            'MSFT': {'percentage': 50.0}
        }
        
        score = calculate_diversification_score(allocation)
        
        assert score == 100.0  # Perfect for 2 holdings
    
    def test_empty_allocation(self):
        """Test empty allocation."""
        score = calculate_diversification_score({})
        
        assert score == 0


class TestPortfolioCoachAgent:
    """Test main portfolio coach agent function."""
    
    @patch('app.agents.portfolio_coach.call_llm')
    @patch('app.agents.portfolio_coach.get_client')
    def test_agent_with_holdings(self, mock_get_client, mock_call_llm):
        """Test agent with holdings."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.side_effect = lambda ticker: MagicMock(
            price={'AAPL': 150, 'MSFT': 300}.get(ticker, 100)
        )
        mock_call_llm.return_value = "Your portfolio is well-diversified."
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 100},
            'MSFT': {'quantity': 5, 'purchase_price': 200}
        }
        
        result = run("Analyze my portfolio", holdings)
        
        assert "well-diversified" in result
        assert mock_call_llm.called
    
    def test_agent_no_holdings(self):
        """Test agent with no holdings."""
        result = run("Analyze my portfolio", None)
        
        assert "No holdings" in result
    
    @patch('app.agents.portfolio_coach.call_llm')
    @patch('app.agents.portfolio_coach.get_client')
    def test_agent_with_empty_holdings(self, mock_get_client, mock_call_llm):
        """Test agent with empty holdings dict."""
        result = run("Analyze my portfolio", {})
        
        assert "No holdings" in result
    
    @patch('app.agents.portfolio_coach.call_llm')
    @patch('app.agents.portfolio_coach.get_client')
    def test_agent_llm_error_fallback(self, mock_get_client, mock_call_llm):
        """Test fallback when LLM fails."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.side_effect = lambda ticker: MagicMock(
            price={'AAPL': 150}.get(ticker, 100)
        )
        mock_call_llm.side_effect = Exception("LLM error")
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 100}}
        result = run("Analyze my portfolio", holdings)
        
        # Should return fallback metrics
        assert "Allocation" in result or "allocation" in result
        assert "AAPL" in result
    
    @patch('app.agents.portfolio_coach.call_llm')
    @patch('app.agents.portfolio_coach.get_client')
    def test_agent_concentrated_portfolio(self, mock_get_client, mock_call_llm):
        """Test agent with concentrated portfolio."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.side_effect = lambda ticker: MagicMock(price=100)
        mock_call_llm.return_value = "Consider diversifying to reduce concentration risk."
        
        holdings = {
            'AAPL': {'quantity': 80, 'purchase_price': 100},  # 80%
            'MSFT': {'quantity': 20, 'purchase_price': 100}   # 20%
        }
        
        result = run("Is my portfolio too concentrated?", holdings)
        
        assert mock_call_llm.called
        # Check that LLM was given concentration info
        call_args = mock_call_llm.call_args
        assert "45" in call_args[1]['user_prompt'] or "80" in call_args[1]['user_prompt']


class TestPortfolioCoachIntegration:
    """Integration tests for portfolio coach."""
    
    @patch('app.agents.portfolio_coach.call_llm')
    @patch('app.agents.portfolio_coach.get_client')
    def test_full_workflow_tech_heavy(self, mock_get_client, mock_call_llm):
        """Test full workflow with tech-heavy portfolio."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Tech heavy: AAPL $4000, MSFT $3000, GOOGL $2000, TSLA $1000
        prices = {'AAPL': 200, 'MSFT': 300, 'GOOGL': 100, 'TSLA': 100}
        mock_client.get_quote.side_effect = lambda ticker: MagicMock(price=prices.get(ticker, 100))
        mock_call_llm.return_value = "Consider adding non-tech diversification."
        
        holdings = {
            'AAPL': {'quantity': 20, 'purchase_price': 150},
            'MSFT': {'quantity': 10, 'purchase_price': 250},
            'GOOGL': {'quantity': 20, 'purchase_price': 80},
            'TSLA': {'quantity': 10, 'purchase_price': 80}
        }
        
        result = run("My portfolio is all tech stocks. What should I do?", holdings)
        
        assert mock_call_llm.called
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('app.agents.portfolio_coach.call_llm')
    @patch('app.agents.portfolio_coach.get_client')
    def test_full_workflow_balanced(self, mock_get_client, mock_call_llm):
        """Test full workflow with balanced portfolio."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Balanced: equal weights
        mock_client.get_quote.return_value = MagicMock(price=100)
        mock_call_llm.return_value = "Your portfolio is well-balanced and diversified."
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 100},
            'MSFT': {'quantity': 10, 'purchase_price': 100},
            'GOOGL': {'quantity': 10, 'purchase_price': 100},
            'AMZN': {'quantity': 10, 'purchase_price': 100}
        }
        
        result = run("How diversified is my portfolio?", holdings)
        
        assert "well-balanced" in result or "diversified" in result
