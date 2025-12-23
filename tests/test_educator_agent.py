from unittest.mock import patch

from app.agents import educator


def test_educator_returns_none_when_no_docs():
    with patch("app.agents.educator.query_rag", return_value=[]):
        assert educator.run("What is diversification?") is None


def test_educator_with_verification_returns_tuple():
    with patch("app.agents.educator.query_rag", return_value=["Doc A", "Doc B"]), \
         patch("app.agents.educator.query_rag_with_scores", return_value=[{"document": "Doc A", "similarity_score": 0.5}]), \
         patch("app.agents.educator.categorize_answer_source", return_value={"category": "RAG_GROUNDED", "confidence": 0.9, "sources": []}):
        ans, ver = educator.run("Explain ETFs", return_verification=True)
        assert isinstance(ans, str)
        assert isinstance(ver, dict)
        assert ver["category"] in {"RAG_GROUNDED", "RAG_INFORMED", "LLM_GENERATED", "RAG_PARTIALLY_MATCHED"}
