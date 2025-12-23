"""
DeepEval sanity checks for remaining agents (strategy, portfolio_coach, risk_profiler, orchestrator).
Runs only if deepeval is installed; all LLM calls are mocked for determinism.
"""
from unittest.mock import patch, MagicMock

import pytest

try:
    from deepeval import evaluate
    from deepeval.metrics import ExactMatchMetric
    from deepeval.test_case import LLMTestCase
    DEEPEVAL_AVAILABLE = True
except ImportError:  # pragma: no cover
    DEEPEVAL_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not DEEPEVAL_AVAILABLE,
    reason="deepeval is required for these tests",
)


def _assert_results(results):
    if results is None:
        return
    if isinstance(results, (list, tuple)):
        for r in results:
            passed = getattr(r, "success", getattr(r, "passed", True))
            assert passed
    else:
        passed = getattr(results, "success", getattr(results, "passed", True))
        assert passed


def test_deepeval_strategy_agent_balanced():
    from app.agents import strategy

    # Mock quote client to avoid external calls
    mock_quote = MagicMock(price=120.0, dividend_yield=1.0)
    with patch("app.agents.strategy.get_client") as mock_client, patch(
        "app.agents.strategy.call_llm", return_value="Balanced strategy summary"
    ):
        mock_client.return_value.get_quote.return_value = mock_quote
        actual = strategy.run(
            "Create a balanced strategy",
            holdings_dict={"AAPL": {"quantity": 10, "purchase_price": 100}},
            strategy_type="balanced",
        )

    expected = "Balanced strategy summary"
    case = LLMTestCase(
        input="Strategy balanced",
        actual_output=actual,
        expected_output=expected,
    )
    results = evaluate([case], metrics=[ExactMatchMetric()])
    _assert_results(results)


def test_deepeval_portfolio_coach():
    from app.agents import portfolio_coach

    mock_quote = MagicMock(price=200.0)
    with patch("app.agents.portfolio_coach.get_client") as mock_client, patch(
        "app.agents.portfolio_coach.call_llm", return_value="Rebalance recommendation"
    ):
        mock_client.return_value.get_quote.return_value = mock_quote
        actual = portfolio_coach.run(
            "Coach my portfolio",
            holdings_dict={"MSFT": {"quantity": 5, "purchase_price": 200}},
        )

    expected = "Rebalance recommendation"
    case = LLMTestCase(
        input="Portfolio coach",
        actual_output=actual,
        expected_output=expected,
    )
    results = evaluate([case], metrics=[ExactMatchMetric()])
    _assert_results(results)


def test_deepeval_risk_profiler():
    from app.agents import risk_profiler

    with patch("app.agents.risk_profiler.call_llm", return_value="Risk profile: MODERATE"):
        actual = risk_profiler.run(
            "Assess my risk",
            holdings_dict={"VOO": {"quantity": 10, "purchase_price": 400}},
        )

    expected = "Risk profile: MODERATE"
    case = LLMTestCase(
        input="Risk profiler",
        actual_output=actual,
        expected_output=expected,
    )
    results = evaluate([case], metrics=[ExactMatchMetric()])
    _assert_results(results)


def test_deepeval_orchestrator_router():
    from app.agents import orchestrator

    # Mock intent classification and agent responses to keep deterministic
    with patch("app.agents.orchestrator.classify_intent", return_value=("ASK_MARKET", "LOW")), patch(
        "app.agents.orchestrator.call_llm", side_effect=['{"plan": ["MarketAgent"]}', "Quote: 100"]
    ), patch("app.agents.orchestrator.market_run", return_value="Quote: 100"), patch(
        "app.agents.orchestrator.get_portfolio_client"
    ) as mock_client, patch("app.agents.orchestrator.compliance_run", return_value="Quote: 100"):
        mock_client.return_value.get_holdings.return_value = {"holdings": {}}
        actual, intent, risk = orchestrator.handle_message("What is AAPL price?", conversation_context=[])

    expected = "Quote: 100"
    case = LLMTestCase(
        input="Orchestrator route",
        actual_output=actual,
        expected_output=expected,
    )
    results = evaluate([case], metrics=[ExactMatchMetric()])
    _assert_results(results)
    assert intent == "ASK_MARKET"
    assert risk == "LOW"
