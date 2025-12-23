"""
Manual RAG verification test. Re-ingests KB and evaluates verification outputs.
Skipped by default; enable with RUN_MANUAL_TESTS=1.
"""
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_MANUAL_TESTS"),
    reason="Manual RAG test requires RUN_MANUAL_TESTS=1 (ingests KB).",
)

from app.rag.ingest import ingest
from app.rag.verification import query_rag_with_scores, categorize_answer_source


def test_rag_verification_manual():
    ingest()
    queries = [
        "What is a stock?",
        "Explain dividends",
        "How does diversification reduce risk?",
    ]

    for q in queries:
        rag_results = query_rag_with_scores(q, k=3)
        ver = categorize_answer_source(rag_results, f"Answer about {q.lower()}")
        assert "category" in ver
        assert "confidence" in ver
