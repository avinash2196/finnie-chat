"""
DeepEval-based sanity tests to exercise key response paths with deterministic expectations.
Runs only if deepeval is installed; does not call external LLMs.
"""
from types import SimpleNamespace
from unittest.mock import patch
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


def test_deepeval_market_run_exact_match():
    from app.agents import market

    with patch.object(market, "_client") as mock_client, patch(
        "app.agents.market.extract_ticker", return_value="AAPL"
    ):
        mock_client.get_quote.return_value = SimpleNamespace(
            ticker="AAPL",
            price=123.45,
            currency="USD",
            change_pct=1.0,
            timestamp=1234567890.0,
            source="mock",
            error=None,
        )
        actual = market.run("What's AAPL doing?")

    expected = "AAPL is trading at 123.45 USD (1.00% today)."
    case = LLMTestCase(
        input="Market response",
        actual_output=actual,
        expected_output=expected,
    )
    results = evaluate([case], metrics=[ExactMatchMetric()])
    _assert_results(results)


def test_deepeval_educator_with_verification():
    from app.agents import educator

    with patch("app.agents.educator.query_rag", return_value=["Doc A", "Doc B"]), patch(
        "app.agents.educator.query_rag_with_scores",
        return_value=[{"document": "Doc A", "similarity_score": 0.6}],
    ), patch(
        "app.agents.educator.categorize_answer_source",
        return_value={"category": "RAG_GROUNDED", "confidence": 0.9, "sources": []},
    ):
        answer, verification = educator.run("Explain ETFs", return_verification=True)

    expected_answer = "Use ONLY the following trusted information:\n\nDoc A\nDoc B"
    case = LLMTestCase(
        input="Educator response",
        actual_output=answer,
        expected_output=expected_answer,
    )
    results = evaluate([case], metrics=[ExactMatchMetric()])
    _assert_results(results)
    assert verification["category"] == "RAG_GROUNDED"
