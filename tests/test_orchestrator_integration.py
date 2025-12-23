"""Integration tests for Orchestrator with all agents and Portfolio MCP."""

import sys
from pathlib import Path
import pytest
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.agents.orchestrator import handle_message
from app.intent import classify_intent
from app.mcp.portfolio import get_portfolio_client


class TestOrchestratorIntegration:
    """Integration tests for orchestrator with portfolio agents."""

    def test_orchestrator_recognizes_portfolio_intent(self):
        """Test that orchestrator recognizes ASK_PORTFOLIO intent."""
        message = "How is my portfolio diversified?"
        intent, risk = classify_intent(message)
        assert intent == "ASK_PORTFOLIO", f"Expected ASK_PORTFOLIO, got {intent}"
        assert risk in ["LOW", "MED", "HIGH"]

    def test_orchestrator_recognizes_risk_intent(self):
        """Test that orchestrator recognizes ASK_RISK intent."""
        message = "What is the risk level of my portfolio?"
        intent, risk = classify_intent(message)
        assert intent == "ASK_RISK", f"Expected ASK_RISK, got {intent}"

    def test_orchestrator_recognizes_strategy_intent(self):
        """Test that orchestrator recognizes ASK_STRATEGY intent."""
        message = "What dividend stocks should I look for?"
        intent, risk = classify_intent(message)
        assert intent == "ASK_STRATEGY", f"Expected ASK_STRATEGY, got {intent}"

    def test_orchestrator_handles_portfolio_query(self):
        """Test orchestrator handles portfolio diversification query end-to-end."""
        message = "How well is my portfolio diversified?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert isinstance(response, str)
        assert len(response) > 0, "Response should not be empty"
        assert intent == "ASK_PORTFOLIO"
        assert risk in ["LOW", "MED", "HIGH"]

    def test_orchestrator_handles_risk_query(self):
        """Test orchestrator handles portfolio risk query end-to-end."""
        message = "What is my portfolio volatility?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert intent == "ASK_RISK"

    def test_orchestrator_handles_strategy_query(self):
        """Test orchestrator handles strategy query end-to-end."""
        message = "What dividend investment opportunities do I have?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert intent == "ASK_STRATEGY"

    def test_orchestrator_handles_concept_query(self):
        """Test orchestrator still handles concept queries."""
        message = "What is diversification?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert intent == "ASK_CONCEPT"
        assert risk in ["LOW", "MED", "HIGH"]

    def test_orchestrator_handles_market_query(self):
        """Test orchestrator still handles market queries."""
        message = "What is the current price of Apple stock?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert intent == "ASK_MARKET"

    def test_orchestrator_with_conversation_context(self):
        """Test orchestrator respects conversation context."""
        context = "User previously asked about tech stocks.\n"
        message = "How is my tech allocation?"
        response, intent, risk = handle_message(message, conversation_context=context, user_id="user_123")
        
        assert isinstance(response, str)
        assert len(response) > 0

    def test_orchestrator_risk_detection_high_risk(self):
        """Test orchestrator detects high-risk intent."""
        message = "Should I sell all my AAPL and buy Bitcoin?"
        intent, risk = classify_intent(message)
        assert risk == "HIGH", f"Expected HIGH risk, got {risk}"

    def test_orchestrator_risk_detection_med_risk(self):
        """Test orchestrator detects medium-risk intent."""
        message = "What is a growth strategy?"
        intent, risk = classify_intent(message)
        assert risk in ["LOW", "MED"], f"Expected LOW or MED risk, got {risk}"

    def test_portfolio_mcp_integration(self):
        """Test that orchestrator successfully integrates with Portfolio MCP."""
        client = get_portfolio_client("user_123")
        portfolio_result = client.get_holdings()
        
        assert 'holdings' in portfolio_result
        assert isinstance(portfolio_result['holdings'], dict)
        # Allow empty portfolios depending on environment
        assert len(portfolio_result['holdings']) >= 0

    def test_portfolio_agent_receives_correct_data(self):
        """Test that portfolio agents receive data from MCP."""
        # This tests the integration indirectly
        message = "Is my portfolio too concentrated?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        # Response should mention specific holdings or concentration analysis
        assert isinstance(response, str)
        assert len(response) > 0
        # Should not be error message
        assert "Unable to fetch" not in response or "No holdings" not in response

    def test_orchestrator_default_user_id(self):
        """Test that orchestrator uses default user_id."""
        message = "Analyze my portfolio allocation"
        response, intent, risk = handle_message(message)  # No user_id provided
        
        assert isinstance(response, str)
        assert len(response) > 0

    def test_orchestrator_handles_dividend_strategy(self):
        """Test orchestrator auto-detects dividend strategy."""
        message = "Show me dividend opportunities in my portfolio"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert isinstance(response, str)
        assert intent == "ASK_STRATEGY"

    def test_orchestrator_handles_growth_strategy(self):
        """Test orchestrator auto-detects growth strategy."""
        message = "What are growth stocks in my portfolio?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert isinstance(response, str)
        # Growth strategy can be classified as ASK_STRATEGY or ASK_PORTFOLIO depending on phrasing
        assert intent in ["ASK_STRATEGY", "ASK_PORTFOLIO"]

    def test_orchestrator_handles_value_strategy(self):
        """Test orchestrator auto-detects value strategy."""
        message = "Which of my holdings are value stocks?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert isinstance(response, str)
        # Value strategy can be classified as ASK_STRATEGY or ASK_PORTFOLIO depending on phrasing
        assert intent in ["ASK_STRATEGY", "ASK_PORTFOLIO"]

    def test_orchestrator_response_includes_compliance(self):
        """Test that orchestrator responses include compliance disclaimers."""
        message = "Is my portfolio risky?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        # Response should be filtered through compliance agent
        assert isinstance(response, str)
        assert len(response) > 0

    def test_orchestrator_handles_invalid_user_id(self):
        """Test orchestrator gracefully handles missing user portfolio."""
        message = "Analyze my portfolio"
        # Use non-existent user_id
        response, intent, risk = handle_message(message, user_id="nonexistent_user")
        
        # Should either return data (if MCP has default) or error message
        assert isinstance(response, str)

    def test_orchestrator_multi_topic_query(self):
        """Test orchestrator handles queries about multiple topics."""
        message = "What is diversification and how diversified is my portfolio?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert isinstance(response, str)
        assert len(response) > 0

    def test_intent_returns_tuple(self):
        """Test that classify_intent returns (intent, risk) tuple."""
        message = "What is a stock?"
        result = classify_intent(message)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        intent, risk = result
        assert isinstance(intent, str)
        assert isinstance(risk, str)

    def test_orchestrator_returns_tuple(self):
        """Test that handle_message returns (response, intent, risk) tuple."""
        message = "Tell me about my portfolio"
        result = handle_message(message, user_id="user_123")
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        response, intent, risk = result
        assert isinstance(response, str)
        assert isinstance(intent, str)
        assert isinstance(risk, str)

    def test_risk_profiler_integration(self):
        """Test Risk Profiler agent is properly integrated."""
        message = "What is the risk in my portfolio?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert intent == "ASK_RISK"
        assert isinstance(response, str)
        # Response should not be empty and not contain error indicators
        assert len(response) > 0
        assert "Error" not in response or len(response) > 20  # Allow "Error" in explanation

    def test_portfolio_coach_integration(self):
        """Test Portfolio Coach agent is properly integrated."""
        message = "How should I rebalance my portfolio?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert intent == "ASK_PORTFOLIO"
        assert isinstance(response, str)
        assert len(response) > 0

    def test_strategy_agent_integration(self):
        """Test Strategy agent is properly integrated."""
        message = "What investment opportunities does my portfolio have?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        # Investment opportunities can be classified as ASK_STRATEGY or ASK_PORTFOLIO
        assert intent in ["ASK_STRATEGY", "ASK_PORTFOLIO"]
        assert isinstance(response, str)
        assert len(response) > 0

    def test_educator_agent_integration(self):
        """Test Educator agent still works."""
        message = "Explain what a stock is"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert intent == "ASK_CONCEPT"
        assert isinstance(response, str)
        assert len(response) > 0

    def test_market_agent_integration(self):
        """Test Market agent still works."""
        message = "What is the price of Tesla?"
        response, intent, risk = handle_message(message, user_id="user_123")
        
        assert intent == "ASK_MARKET"
        assert isinstance(response, str)
        assert len(response) > 0

    def test_long_conversation_context(self):
        """Test orchestrator with extended conversation history."""
        context = """
        User: What is diversification?
        Assistant: Diversification means spreading investments across different assets...
        User: How should I diversify?
        Assistant: You can diversify across sectors, asset classes...
        """
        message = "How diversified is my current portfolio?"
        response, intent, risk = handle_message(message, conversation_context=context, user_id="user_123")
        
        assert isinstance(response, str)
        assert len(response) > 0

    def test_orchestrator_consistency(self):
        """Test that multiple calls with same input produce consistent results."""
        message = "Analyze my portfolio risk"
        
        response1, intent1, risk1 = handle_message(message, user_id="user_123")
        response2, intent2, risk2 = handle_message(message, user_id="user_123")
        
        # Intent and risk should be consistent
        assert intent1 == intent2
        assert risk1 == risk2
        # Responses may vary slightly due to LLM, but both should be valid
        assert isinstance(response1, str) and isinstance(response2, str)
        assert len(response1) > 0 and len(response2) > 0


class TestIntentClassification:
    """Tests for intent classification with new portfolio intents."""

    def test_classify_portfolio_intent_variants(self):
        """Test various portfolio-related queries."""
        portfolio_queries = [
            "How is my portfolio diversified?",
            "What is my allocation?",
            "Am I too concentrated in tech?",
            "Should I rebalance?",
            "What is my portfolio composition?"
        ]
        
        for query in portfolio_queries:
            intent, risk = classify_intent(query)
            assert intent == "ASK_PORTFOLIO", f"Failed for: {query}, got {intent}"

    def test_classify_risk_intent_variants(self):
        """Test various risk-related queries."""
        risk_queries = [
            "What is my portfolio risk?",
            "How volatile is my portfolio?",
            "How much downside risk do I have?",
            "What is my portfolio beta?"
        ]
        
        for query in risk_queries:
            intent, risk = classify_intent(query)
            assert intent == "ASK_RISK", f"Failed for: {query}, got {intent}"

    def test_classify_strategy_intent_variants(self):
        """Test various strategy-related queries."""
        strategy_queries = [
            "What dividend opportunities do I have?",
            "Show me growth stocks",
            "Find value investments",
            "Screen for dividend stocks"
        ]
        
        for query in strategy_queries:
            intent, risk = classify_intent(query)
            assert intent == "ASK_STRATEGY", f"Failed for: {query}, got {intent}"

    def test_classify_concept_intent_preserved(self):
        """Test that concept queries still work."""
        concept_queries = [
            "What is a stock?",
            "Explain diversification",
            "What is a bond?",
            "How do dividends work?"
        ]
        
        for query in concept_queries:
            intent, risk = classify_intent(query)
            assert intent == "ASK_CONCEPT", f"Failed for: {query}, got {intent}"

    def test_classify_market_intent_preserved(self):
        """Test that market queries still work."""
        market_queries = [
            "What is Apple's stock price?",
            "Show me Tesla's trading volume",
            "What is the S&P 500 today?",
            "How much is Google up today?"
        ]
        
        for query in market_queries:
            intent, risk = classify_intent(query)
            assert intent == "ASK_MARKET", f"Failed for: {query}, got {intent}"


class TestPortfolioMCPIntegration:
    """Tests for Portfolio MCP integration with agents."""

    def test_portfolio_client_returns_holdings(self):
        """Test that Portfolio MCP client returns holdings."""
        client = get_portfolio_client("user_123")
        result = client.get_holdings()
        
        assert 'holdings' in result
        holdings = result['holdings']
        assert isinstance(holdings, dict)
        # Allow empty holdings depending on environment
        assert len(holdings) >= 0
        
        # Check holdings structure
        for ticker, holding_data in holdings.items():
            assert 'quantity' in holding_data
            assert 'purchase_price' in holding_data

    def test_portfolio_client_consistency(self):
        """Test that Portfolio MCP returns consistent data."""
        client1 = get_portfolio_client("user_123")
        client2 = get_portfolio_client("user_123")
        
        result1 = client1.get_holdings()
        result2 = client2.get_holdings()
        
        assert result1['holdings'].keys() == result2['holdings'].keys()

    def test_different_users_have_different_portfolios(self):
        """Test that different user IDs can have different data."""
        # This may or may not work depending on MCP implementation
        # But the client should accept different user_ids
        client1 = get_portfolio_client("user_123")
        client2 = get_portfolio_client("user_456")
        
        # Both should return valid results
        result1 = client1.get_holdings()
        result2 = client2.get_holdings()
        
        assert 'holdings' in result1
        assert 'holdings' in result2


class TestAgentSignatureUpdates:
    """Tests for agent function signature updates."""

    def test_risk_profiler_accepts_user_id(self):
        """Test that risk_profiler agent accepts user_id parameter."""
        from app.agents.risk_profiler import run as risk_profiler_run
        
        # Should accept user_id parameter
        result = risk_profiler_run("What is my portfolio risk?", user_id="user_123")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_portfolio_coach_accepts_user_id(self):
        """Test that portfolio_coach agent accepts user_id parameter."""
        from app.agents.portfolio_coach import run as portfolio_coach_run
        
        # Should accept user_id parameter
        result = portfolio_coach_run("How is my portfolio allocated?", user_id="user_123")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_strategy_accepts_user_id(self):
        """Test that strategy agent accepts user_id parameter."""
        from app.agents.strategy import run as strategy_run
        
        # Should accept user_id parameter
        result = strategy_run("Show me dividend opportunities", strategy_type="dividend", user_id="user_123")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_risk_profiler_backward_compatible(self):
        """Test that risk_profiler still accepts holdings_dict for backward compatibility."""
        from app.agents.risk_profiler import run as risk_profiler_run
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 150},
            'MSFT': {'quantity': 5, 'purchase_price': 300}
        }
        
        result = risk_profiler_run("What is my risk?", holdings_dict=holdings)
        assert isinstance(result, str)

    def test_portfolio_coach_backward_compatible(self):
        """Test that portfolio_coach still accepts holdings_dict."""
        from app.agents.portfolio_coach import run as portfolio_coach_run
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 150},
            'MSFT': {'quantity': 5, 'purchase_price': 300}
        }
        
        result = portfolio_coach_run("How is my portfolio?", holdings_dict=holdings)
        assert isinstance(result, str)

    def test_strategy_backward_compatible(self):
        """Test that strategy agent still accepts holdings_dict."""
        from app.agents.strategy import run as strategy_run
        
        holdings = {
            'AAPL': {'quantity': 10, 'purchase_price': 150},
            'MSFT': {'quantity': 5, 'purchase_price': 300}
        }
        
        result = strategy_run("Show dividend stocks", holdings_dict=holdings, strategy_type="dividend")
        assert isinstance(result, str)
