"""Unit and integration tests for Strategy Agent."""

import pytest
from unittest.mock import patch, MagicMock
from app.agents.strategy import (
    run_dividend_screener,
    run_growth_screener,
    run_value_screener,
    run
)


class TestDividendScreener:
    """Test dividend screening function."""
    
    @patch('app.agents.strategy.get_client')
    def test_basic_dividend_screening(self, mock_get_client):
        """Test basic dividend screening."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock quotes with dividend yields
        def quote_side_effect(ticker):
            quotes = {
                'AAPL': MagicMock(price=150, dividend_yield=0.5),
                'MSFT': MagicMock(price=300, dividend_yield=0.8),
                'GOOGL': MagicMock(price=100, dividend_yield=0)
            }
            return quotes.get(ticker, MagicMock(price=100, dividend_yield=0))
        
        mock_client.get_quote.side_effect = quote_side_effect
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 100},
            'MSFT': {'quantity': 5, 'purchase_price': 200},
            'GOOGL': {'quantity': 20, 'purchase_price': 80}
        }
        
        result = run_dividend_screener(holdings)
        
        assert result['error'] is None
        assert len(result['opportunities']) == 3
        assert result['total_dividend_income'] > 0
        # AAPL: 10 * 150 * 0.005 = 7.5
        # MSFT: 5 * 300 * 0.008 = 12
        # GOOGL: 20 * 100 * 0 = 0
        assert result['total_dividend_income'] == 19.5
    
    @patch('app.agents.strategy.get_client')
    def test_no_dividend_holdings(self, mock_get_client):
        """Test with holdings that don't pay dividends."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=100, dividend_yield=0)
        
        holdings = {
            'GOOGL': {'quantity': 10, 'purchase_price': 80},
            'AMZN': {'quantity': 5, 'purchase_price': 100}
        }
        
        result = run_dividend_screener(holdings)
        
        assert result['error'] is None
        assert result['total_dividend_income'] == 0
    
    @patch('app.agents.strategy.get_client')
    def test_empty_holdings(self, mock_get_client):
        """Test with empty holdings."""
        result = run_dividend_screener({})
        
        assert result['error'] is None
        assert result['opportunities'] == []
        assert result['total_dividend_income'] == 0
    
    @patch('app.agents.strategy.get_client')
    def test_quote_fetch_error(self, mock_get_client):
        """Test error handling when quote fetch fails."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=None)
        
        holdings = {'INVALID': {'quantity': 10, 'purchase_price': 100}}
        result = run_dividend_screener(holdings)
        
        assert result['error'] is None
        assert len(result['opportunities']) == 0


class TestGrowthScreener:
    """Test growth screening function."""
    
    @patch('app.agents.strategy.get_client')
    def test_growth_screening_positive_returns(self, mock_get_client):
        """Test growth screening with positive returns."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        def quote_side_effect(ticker):
            prices = {
                'AAPL': 200,    # +100% gain: (200-100)*10 = 1000
                'MSFT': 400,    # +100% gain: (400-200)*5 = 1000
                'GOOGL': 80     # -20% loss: (80-100)*20 = -400
            }
            return MagicMock(price=prices.get(ticker, 100))
        
        mock_client.get_quote.side_effect = quote_side_effect
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 100},
            'MSFT': {'quantity': 5, 'purchase_price': 200},
            'GOOGL': {'quantity': 20, 'purchase_price': 100}
        }
        
        result = run_growth_screener(holdings)
        
        assert result['error'] is None
        assert len(result['all_holdings']) == 3
        assert len(result['top_performers']) == 2  # AAPL and MSFT have positive returns
        assert result['top_performers'][0]['ticker'] in ['AAPL', 'MSFT']
        # Total gains: 1000 (AAPL) + 1000 (MSFT) - 400 (GOOGL) = 1600
        assert result['total_unrealized_gains'] == 1600
    
    @patch('app.agents.strategy.get_client')
    def test_growth_screening_no_gains(self, mock_get_client):
        """Test growth screening with no gains."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=90)
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 100},
            'MSFT': {'quantity': 5, 'purchase_price': 100}
        }
        
        result = run_growth_screener(holdings)
        
        assert result['error'] is None
        assert len(result['top_performers']) == 0
        # Total losses: (90-100)*10 + (90-100)*5 = -100 - 50 = -150
        assert result['total_unrealized_gains'] == -150
    
    @patch('app.agents.strategy.get_client')
    def test_growth_screening_top_3_limit(self, mock_get_client):
        """Test that only top 3 performers are returned."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # All with gains
        mock_client.get_quote.side_effect = lambda ticker: MagicMock(
            price=150
        )
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 100},
            'MSFT': {'quantity': 10, 'purchase_price': 100},
            'GOOGL': {'quantity': 10, 'purchase_price': 100},
            'AMZN': {'quantity': 10, 'purchase_price': 100},
            'TSLA': {'quantity': 10, 'purchase_price': 100}
        }
        
        result = run_growth_screener(holdings)
        
        assert len(result['all_holdings']) == 5
        assert len(result['top_performers']) == 3  # Limited to top 3


class TestValueScreener:
    """Test value screening function."""
    
    @patch('app.agents.strategy.get_client')
    def test_value_screening_undervalued(self, mock_get_client):
        """Test value screening for undervalued stocks."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        def quote_side_effect(ticker):
            prices = {
                'AAPL': 80,     # -20% discount
                'MSFT': 150,    # -25% discount
                'GOOGL': 120    # +20% premium
            }
            return MagicMock(price=prices.get(ticker, 100))
        
        mock_client.get_quote.side_effect = quote_side_effect
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 100},
            'MSFT': {'quantity': 5, 'purchase_price': 200},
            'GOOGL': {'quantity': 20, 'purchase_price': 100}
        }
        
        result = run_value_screener(holdings)
        
        assert result['error'] is None
        assert len(result['all_holdings']) == 3
        assert len(result['bargain_opportunities']) == 2  # AAPL and MSFT are undervalued
        assert result['bargain_opportunities'][0]['is_undervalued'] is True
    
    @patch('app.agents.strategy.get_client')
    def test_value_screening_no_bargains(self, mock_get_client):
        """Test value screening with no undervalued stocks."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=150)
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 100},
            'MSFT': {'quantity': 5, 'purchase_price': 100}
        }
        
        result = run_value_screener(holdings)
        
        assert result['error'] is None
        assert len(result['bargain_opportunities']) == 0
    
    @patch('app.agents.strategy.get_client')
    def test_value_screening_discount_sorting(self, mock_get_client):
        """Test that bargains are sorted by discount (biggest first)."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        def quote_side_effect(ticker):
            prices = {
                'AAPL': 50,     # -50% discount
                'MSFT': 90,     # -10% discount
                'GOOGL': 60     # -40% discount
            }
            return MagicMock(price=prices.get(ticker, 100))
        
        mock_client.get_quote.side_effect = quote_side_effect
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 100},
            'MSFT': {'quantity': 5, 'purchase_price': 100},
            'GOOGL': {'quantity': 20, 'purchase_price': 100}
        }
        
        result = run_value_screener(holdings)
        
        assert len(result['bargain_opportunities']) == 3
        # First should be AAPL (-50%), then GOOGL (-40%), then MSFT (-10%)
        assert result['bargain_opportunities'][0]['ticker'] == 'AAPL'
        assert result['bargain_opportunities'][0]['discount_pct'] == 50.0


class TestStrategyAgent:
    """Test main strategy agent function."""
    
    @patch('app.agents.strategy.get_portfolio_client')
    @patch('app.agents.strategy.call_llm')
    @patch('app.agents.strategy.get_client')
    def test_agent_no_holdings(self, mock_get_client, mock_call_llm, mock_portfolio_client):
        """Test agent with no holdings - now fetches from MCP by default."""
        # Mock the Portfolio MCP client
        mock_portfolio_obj = MagicMock()
        mock_portfolio_obj.get_holdings.return_value = {
            'holdings': {
                'AAPL': {'quantity': 10, 'purchase_price': 150},
                'MSFT': {'quantity': 5, 'purchase_price': 300}
            }
        }
        mock_portfolio_client.return_value = mock_portfolio_obj
        
        # Mock the Market client - return proper quote object with all attributes
        def get_quote_side_effect(ticker):
            mock_quote = MagicMock()
            mock_quote.price = 180.0
            mock_quote.dividend_yield = 2.5
            return mock_quote
        
        mock_market_obj = MagicMock()
        mock_market_obj.get_quote.side_effect = get_quote_side_effect
        mock_get_client.return_value = mock_market_obj
        
        # Mock LLM response
        mock_call_llm.return_value = "Strategy analysis complete"
        
        # When holdings_dict=None, the agent fetches from Portfolio MCP using default user_id
        result = run("What strategy should I follow?", None)
        
        # Should get a valid response (from MCP default user data, not an error)
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('app.agents.strategy.call_llm')
    @patch('app.agents.strategy.get_client')
    def test_agent_dividend_strategy(self, mock_get_client, mock_call_llm):
        """Test agent with dividend strategy."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=100, dividend_yield=0.5)
        mock_call_llm.return_value = "Consider increasing dividend-paying positions."
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 100}}
        result = run("Focus on dividend income", holdings, strategy_type="dividend")
        
        assert mock_call_llm.called
        assert isinstance(result, str)
    
    @patch('app.agents.strategy.call_llm')
    @patch('app.agents.strategy.get_client')
    def test_agent_growth_strategy(self, mock_get_client, mock_call_llm):
        """Test agent with growth strategy."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=150)
        mock_call_llm.return_value = "Your portfolio has strong growth momentum."
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 100}}
        result = run("Focus on growth", holdings, strategy_type="growth")
        
        assert mock_call_llm.called
        assert isinstance(result, str)
    
    @patch('app.agents.strategy.call_llm')
    @patch('app.agents.strategy.get_client')
    def test_agent_value_strategy(self, mock_get_client, mock_call_llm):
        """Test agent with value strategy."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=80)
        mock_call_llm.return_value = "Several opportunities for value investing."
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 100}}
        result = run("Find undervalued stocks", holdings, strategy_type="value")
        
        assert mock_call_llm.called
        assert isinstance(result, str)
    
    @patch('app.agents.strategy.call_llm')
    @patch('app.agents.strategy.get_client')
    def test_agent_balanced_strategy(self, mock_get_client, mock_call_llm):
        """Test agent with balanced strategy (default)."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=120, dividend_yield=0.5)
        mock_call_llm.return_value = "A balanced approach is recommended."
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 100}}
        result = run("What's the best strategy?", holdings)
        
        assert mock_call_llm.called
        # Should have called run_dividend_screener, run_growth_screener, run_value_screener
        assert isinstance(result, str)
    
    @patch('app.agents.strategy.call_llm')
    @patch('app.agents.strategy.get_client')
    def test_agent_invalid_strategy_type(self, mock_get_client, mock_call_llm):
        """Test agent with invalid strategy type (should default to balanced)."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=100, dividend_yield=0)
        mock_call_llm.return_value = "Balanced strategy applied."
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 100}}
        result = run("Analyze my portfolio", holdings, strategy_type="invalid")
        
        # Should default to balanced and still work
        assert isinstance(result, str)
    
    @patch('app.agents.strategy.call_llm')
    @patch('app.agents.strategy.get_client')
    def test_agent_llm_error_fallback(self, mock_get_client, mock_call_llm):
        """Test fallback when LLM fails."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_quote.return_value = MagicMock(price=100, dividend_yield=0)
        mock_call_llm.side_effect = Exception("LLM error")
        
        holdings = {'AAPL': {'quantity': 10, 'purchase_price': 100}}
        result = run("Analyze my portfolio", holdings, strategy_type="dividend")
        
        # Should return fallback response with screening data
        assert "Strategy Analysis" in result
        assert "DIVIDEND" in result


class TestStrategyIntegration:
    """Integration tests for strategy agent."""
    
    @patch('app.agents.strategy.call_llm')
    @patch('app.agents.strategy.get_client')
    def test_full_workflow_mixed_portfolio(self, mock_get_client, mock_call_llm):
        """Test full workflow with mixed portfolio."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        def quote_side_effect(ticker):
            quotes = {
                'AAPL': MagicMock(price=200, dividend_yield=0.5),   # Growth + dividend
                'MSFT': MagicMock(price=250, dividend_yield=0.8),   # Growth + dividend
                'GOOGL': MagicMock(price=80, dividend_yield=0),     # Value opportunity
                'JNJ': MagicMock(price=150, dividend_yield=2.5),    # Dividend focused
                'TSLA': MagicMock(price=300, dividend_yield=0)      # Growth focused
            }
            return quotes.get(ticker, MagicMock(price=100, dividend_yield=0))
        
        mock_client.get_quote.side_effect = quote_side_effect
        mock_call_llm.return_value = "Diversified strategy recommended across all styles."
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 100},
            'MSFT': {'quantity': 5, 'purchase_price': 200},
            'GOOGL': {'quantity': 20, 'purchase_price': 100},
            'JNJ': {'quantity': 15, 'purchase_price': 150},
            'TSLA': {'quantity': 2, 'purchase_price': 200}
        }
        
        result = run("Create a balanced strategy", holdings, strategy_type="balanced")
        
        assert mock_call_llm.called
        assert isinstance(result, str)
        assert "Diversified" in result or "diversified" in result or "balanced" in result
    
    @patch('app.agents.strategy.call_llm')
    @patch('app.agents.strategy.get_client')
    def test_full_workflow_dividend_focused(self, mock_get_client, mock_call_llm):
        """Test full workflow for dividend-focused investor."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        def quote_side_effect(ticker):
            quotes = {
                'JNJ': MagicMock(price=160, dividend_yield=2.5),
                'KO': MagicMock(price=60, dividend_yield=3.0),
                'PG': MagicMock(price=150, dividend_yield=2.2)
            }
            return quotes.get(ticker, MagicMock(price=100, dividend_yield=0))
        
        mock_client.get_quote.side_effect = quote_side_effect
        mock_call_llm.return_value = "Strong dividend portfolio. Consider adding to diversify."
        
        holdings = {
            'JNJ': {'quantity': 50, 'purchase_price': 150},
            'KO': {'quantity': 100, 'purchase_price': 55},
            'PG': {'quantity': 30, 'purchase_price': 140}
        }
        
        result = run("Maximize dividend income", holdings, strategy_type="dividend")
        
        assert "dividend" in result.lower() or "Dividend" in result
    
    @patch('app.agents.strategy.call_llm')
    @patch('app.agents.strategy.get_client')
    def test_full_workflow_value_focused(self, mock_get_client, mock_call_llm):
        """Test full workflow for value-focused investor."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        def quote_side_effect(ticker):
            quotes = {
                'BAC': MagicMock(price=25, dividend_yield=2.8),      # Down from 35
                'GE': MagicMock(price=80, dividend_yield=1.5),       # Down from 100
                'F': MagicMock(price=8, dividend_yield=4.5)          # Down from 12
            }
            return quotes.get(ticker, MagicMock(price=100, dividend_yield=0))
        
        mock_client.get_quote.side_effect = quote_side_effect
        mock_call_llm.return_value = "Several value opportunities. BAC and GE are attractive."
        
        holdings = {
            'BAC': {'quantity': 100, 'purchase_price': 35},
            'GE': {'quantity': 50, 'purchase_price': 100},
            'F': {'quantity': 500, 'purchase_price': 12}
        }
        
        result = run("Find value opportunities", holdings, strategy_type="value")
        
        assert "value" in result.lower() or "Value" in result
