import pytest
from unittest.mock import patch, MagicMock
from app.agents import educator


def test_run_returns_none_when_no_docs():
    with patch('app.agents.educator.query_rag', return_value=[]):
        assert educator.run("Anything") is None


def test_run_return_verification_branch():
    docs = ["Doc A", "Doc B"]
    with patch('app.agents.educator.query_rag', return_value=docs), \
         patch('app.agents.educator.query_rag_with_scores', return_value=[{'document': 'Doc A', 'score': 0.9}]), \
         patch('app.agents.educator.categorize_answer_source', return_value={'category': 'RAG_GROUNDED', 'confidence': 0.9, 'sources': []}):
        answer, verification = educator.run("Explain ETFs", return_verification=True)
        assert isinstance(answer, str)
        assert verification['category'] == 'RAG_GROUNDED'
