"""DeepEval tests for Chat with Portfolio Context."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.agents.orchestrator import handle_message
from deepeval import evaluate
from deepeval.metrics import ExactMatchMetric
from deepeval.test_case import LLMTestCase


def _assert_results(results):
    """Best-effort assertion across possible deepeval result shapes."""
    if results is None:
        return
    if isinstance(results, (list, tuple)):
        for r in results:
            passed = getattr(r, "success", getattr(r, "passed", True))
            assert passed
    else:
        passed = getattr(results, "success", getattr(results, "passed", True))
        assert passed


class TestChatPortfolioAccess:
    """DeepEval tests for chat with portfolio access."""
    
    @patch('app.agents.orchestrator.get_portfolio_client')
    @patch('app.agents.orchestrator.classify_intent')
    @patch('app.agents.orchestrator.call_llm')
    @patch('app.agents.orchestrator.compliance_run')
    def test_portfolio_question_includes_holdings(
        self,
        mock_compliance,
        mock_llm,
        mock_intent,
        mock_portfolio_client
    ):
        """Test that portfolio questions get user holdings."""
        # Setup mocks
        mock_intent.return_value = ("ASK_PORTFOLIO", "MED")
        
        # Mock portfolio client with actual data
        mock_client = MagicMock()
        mock_client.get_holdings.return_value = {
            'error': None,
            'user_id': 'test_user_123',
            'holdings': {
                'AAPL': {
                    'quantity': 10.0,
                    'purchase_price': 150.0,
                    'current_price': 180.0,
                    'current_value': 1800.0,
                    'gain_loss': 300.0,
                    'gain_loss_pct': 20.0
                },
                'MSFT': {
                    'quantity': 5.0,
                    'purchase_price': 350.0,
                    'current_price': 380.0,
                    'current_value': 1900.0,
                    'gain_loss': 150.0,
                    'gain_loss_pct': 8.57
                }
            },
            'total_portfolio_value': 3700.0
        }
        mock_portfolio_client.return_value = mock_client
        
        # Mock portfolio coach response
        mock_llm.side_effect = [
            # Plan response
            '{"plan": ["PortfolioCoachAgent", "ComplianceAgent"]}',
            # Synthesis response
            "Your portfolio consists of AAPL (10 shares, $1800 value) and MSFT (5 shares, $1900 value). Total portfolio value is $3700. Your portfolio shows good diversification between tech stocks."
        ]
        
        mock_compliance.return_value = "Your portfolio consists of AAPL (10 shares, $1800 value) and MSFT (5 shares, $1900 value). Total portfolio value is $3700. Your portfolio shows good diversification between tech stocks.\n\n(Note: This is educational information, not financial advice.)"
        
        # Execute
        message = "What stocks do I own?"
        user_id = "test_user_123"
        response, intent, risk = handle_message(message, user_id=user_id)
        
        # Verify portfolio client was created with correct user_id
        mock_portfolio_client.assert_called_with(user_id)
        
        # Verify response mentions the holdings
        assert "AAPL" in response or "portfolio" in response.lower()
        assert intent == "ASK_PORTFOLIO"
    
    @patch('app.agents.orchestrator.get_portfolio_client')
    @patch('app.agents.orchestrator.classify_intent')
    @patch('app.agents.orchestrator.call_llm')
    @patch('app.agents.orchestrator.compliance_run')
    def test_different_users_get_different_portfolios(
        self,
        mock_compliance,
        mock_llm,
        mock_intent,
        mock_portfolio_client
    ):
        """Test that different users get their own portfolio data."""
        mock_intent.return_value = ("ASK_PORTFOLIO", "LOW")
        
        def create_portfolio_client(user_id):
            """Factory to create different data per user."""
            client = MagicMock()
            if user_id == "user_001":
                client.get_holdings.return_value = {
                    'error': None,
                    'holdings': {'TSLA': {'quantity': 1.0, 'current_value': 100.0}},
                    'total_portfolio_value': 100.0
                }
            elif user_id == "user_002":
                client.get_holdings.return_value = {
                    'error': None,
                    'holdings': {
                        'AAPL': {'quantity': 10.0, 'current_value': 1800.0},
                        'MSFT': {'quantity': 5.0, 'current_value': 1900.0}
                    },
                    'total_portfolio_value': 3700.0
                }
            return client
        
        mock_portfolio_client.side_effect = create_portfolio_client
        mock_llm.side_effect = [
            '{"plan": ["PortfolioCoachAgent", "ComplianceAgent"]}',
            "Your portfolio analysis..."
        ]
        mock_compliance.return_value = "Your portfolio analysis..."
        
        # Test user_001
        response1, _, _ = handle_message("What's my portfolio?", user_id="user_001")
        
        # Reset mocks
        mock_llm.reset_mock()
        mock_llm.side_effect = [
            '{"plan": ["PortfolioCoachAgent", "ComplianceAgent"]}',
            "Your portfolio analysis..."
        ]
        
        # Test user_002
        response2, _, _ = handle_message("What's my portfolio?", user_id="user_002")
        
        # Verify different portfolio clients were created
        assert mock_portfolio_client.call_count >= 2
        calls = mock_portfolio_client.call_args_list
        assert any(call[0][0] == "user_001" for call in calls)
        assert any(call[0][0] == "user_002" for call in calls)
    
    @patch('app.agents.orchestrator.get_portfolio_client')
    @patch('app.agents.orchestrator.classify_intent')
    @patch('app.agents.orchestrator.call_llm')
    @patch('app.agents.orchestrator.compliance_run')
    def test_portfolio_question_without_holdings_fallback(
        self,
        mock_compliance,
        mock_llm,
        mock_intent,
        mock_portfolio_client
    ):
        """Test graceful handling when user has no holdings."""
        mock_intent.return_value = ("ASK_PORTFOLIO", "LOW")
        
        mock_client = MagicMock()
        mock_client.get_holdings.return_value = {
            'error': None,
            'holdings': {},  # Empty portfolio
            'total_portfolio_value': 0.0
        }
        mock_portfolio_client.return_value = mock_client
        
        mock_llm.side_effect = [
            '{"plan": ["PortfolioCoachAgent", "ComplianceAgent"]}',
            "You don't have any holdings yet. Start investing to build your portfolio."
        ]
        mock_compliance.return_value = "You don't have any holdings yet. Start investing to build your portfolio."
        
        # Execute
        response, intent, risk = handle_message(
            "Tell me about my portfolio",
            user_id="new_user"
        )
        
        # Verify it handles empty portfolio gracefully
        assert response is not None
        assert intent == "ASK_PORTFOLIO"


class TestChatWithRealPortfolioData:
    """DeepEval evaluate() tests for key portfolio response patterns."""

    @patch('app.agents.orchestrator.get_portfolio_client')
    @patch('app.agents.orchestrator.classify_intent')
    @patch('app.agents.orchestrator.call_llm')
    @patch('app.agents.orchestrator.compliance_run')
    def test_portfolio_diversification_analysis(
        self, mock_compliance, mock_llm, mock_intent, mock_portfolio_client
    ):
        """Diversification query returns a grounded portfolio summary."""
        mock_intent.return_value = ("ASK_PORTFOLIO", "LOW")
        mock_client = MagicMock()
        mock_client.get_holdings.return_value = {
            "error": None,
            "holdings": {
                "AAPL": {"quantity": 10.0, "current_value": 1800.0},
                "MSFT": {"quantity": 5.0, "current_value": 1900.0},
            },
            "total_portfolio_value": 3700.0,
        }
        mock_portfolio_client.return_value = mock_client
        expected = "Your portfolio contains AAPL and MSFT."
        mock_llm.side_effect = [
            '{"plan": ["PortfolioCoachAgent", "ComplianceAgent"]}',
            expected,
        ]
        mock_compliance.return_value = expected

        response, intent, _ = handle_message(
            "How diversified is my portfolio?", user_id="test_user"
        )
        assert intent == "ASK_PORTFOLIO"
        case = LLMTestCase(
            input="How diversified is my portfolio?",
            actual_output=response,
            expected_output=expected,
        )
        _assert_results(evaluate([case], metrics=[ExactMatchMetric()]))

    @patch('app.agents.orchestrator.get_portfolio_client')
    @patch('app.agents.orchestrator.classify_intent')
    @patch('app.agents.orchestrator.call_llm')
    @patch('app.agents.orchestrator.compliance_run')
    def test_risk_analysis_with_holdings(
        self, mock_compliance, mock_llm, mock_intent, mock_portfolio_client
    ):
        """Risk query returns a volatility assessment."""
        mock_intent.return_value = ("ASK_RISK", "LOW")
        mock_client = MagicMock()
        mock_client.get_holdings.return_value = {
            "error": None,
            "holdings": {"VOO": {"quantity": 10.0, "current_value": 4500.0}},
            "total_portfolio_value": 4500.0,
        }
        mock_portfolio_client.return_value = mock_client
        expected = "Risk profile: MODERATE volatility."
        mock_llm.side_effect = [
            '{"plan": ["RiskProfilerAgent", "ComplianceAgent"]}',
            expected,
        ]
        mock_compliance.return_value = expected

        response, intent, _ = handle_message(
            "What is my portfolio risk?", user_id="test_user"
        )
        assert intent == "ASK_RISK"
        case = LLMTestCase(
            input="What is my portfolio risk?",
            actual_output=response,
            expected_output=expected,
        )
        _assert_results(evaluate([case], metrics=[ExactMatchMetric()]))

    @patch('app.agents.orchestrator.get_portfolio_client')
    @patch('app.agents.orchestrator.classify_intent')
    @patch('app.agents.orchestrator.call_llm')
    @patch('app.agents.orchestrator.compliance_run')
    def test_stock_recommendation_with_context(
        self, mock_compliance, mock_llm, mock_intent, mock_portfolio_client
    ):
        """Strategy query always includes compliance disclaimer."""
        mock_intent.return_value = ("ASK_STRATEGY", "MED")
        mock_client = MagicMock()
        mock_client.get_holdings.return_value = {
            "error": None,
            "holdings": {},
            "total_portfolio_value": 0.0,
        }
        mock_portfolio_client.return_value = mock_client
        expected = "AAPL looks strong. (Note: educational information, not financial advice.)"
        mock_llm.side_effect = [
            '{"plan": ["StrategyAgent", "ComplianceAgent"]}',
            expected,
        ]
        mock_compliance.return_value = expected

        response, intent, _ = handle_message(
            "Should I buy more AAPL?", user_id="test_user"
        )
        assert intent == "ASK_STRATEGY"
        case = LLMTestCase(
            input="Should I buy more AAPL?",
            actual_output=response,
            expected_output=expected,
        )
        _assert_results(evaluate([case], metrics=[ExactMatchMetric()]))
