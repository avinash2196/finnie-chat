"""
Tests for Retriever Abstraction Layer (RAG)

Covers:
- HybridRetriever (TF-IDF + semantic blending)
- TFIDFRetriever (pure TF-IDF)
- SemanticRetriever (pure semantic)
- RetrievalResult dataclass
- get_retriever() factory function
"""

import pytest
from typing import List
from app.rag.retriever import (
    HybridRetriever,
    TFIDFRetriever,
    SemanticRetriever,
    RetrievalResult,
    get_retriever,
    query_rag_with_scores,
)
from app.rag import store


class TestRetrievalResult:
    """Test RetrievalResult dataclass"""

    def test_retrieval_result_creation(self):
        """Test creating a RetrievalResult"""
        result = RetrievalResult(
            document="Sample document",
            similarity_score=0.95,
            index=0,
            source="hybrid"
        )
        assert result.document == "Sample document"
        assert result.similarity_score == 0.95
        assert result.index == 0
        assert result.source == "hybrid"

    def test_retrieval_result_default_source(self):
        """Test RetrievalResult with default source"""
        result = RetrievalResult(
            document="Test",
            similarity_score=0.5,
            index=1
        )
        assert result.source == "unknown"


class TestHybridRetriever:
    """Test Hybrid Retriever"""

    @pytest.fixture(autouse=True)
    def setup_documents(self):
        """Setup test documents"""
        test_docs = [
            "A bond is a fixed-income security",
            "A stock represents ownership in a company",
            "A mutual fund pools money from investors",
            "Diversification reduces portfolio risk",
            "Asset allocation is key to long-term success"
        ]
        store.documents = test_docs
        store.add_documents(test_docs)
        yield
        # Cleanup
        store.documents = []

    def test_hybrid_retriever_initialization(self):
        """Test HybridRetriever can be initialized"""
        retriever = HybridRetriever()
        assert retriever is not None
        assert hasattr(retriever, 'retrieve')

    def test_hybrid_retriever_retrieve(self):
        """Test HybridRetriever retrieval"""
        retriever = HybridRetriever()
        results = retriever.retrieve("What is a bond?", k=2)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, RetrievalResult) for r in results)
        assert all(0 <= r.similarity_score <= 1 for r in results)
        assert results[0].similarity_score >= results[-1].similarity_score  # Sorted

    def test_hybrid_retriever_k_parameter(self):
        """Test k parameter limits results"""
        retriever = HybridRetriever()
        
        results_k1 = retriever.retrieve("diversification", k=1)
        results_k3 = retriever.retrieve("diversification", k=3)
        
        assert len(results_k1) <= 1
        assert len(results_k3) <= 3
        assert len(results_k1) <= len(results_k3)

    def test_hybrid_retriever_empty_query(self):
        """Test HybridRetriever with empty query"""
        retriever = HybridRetriever()
        results = retriever.retrieve("", k=2)
        
        # Should return something (even if empty query)
        assert isinstance(results, list)


class TestTFIDFRetriever:
    """Test TF-IDF Retriever"""

    @pytest.fixture(autouse=True)
    def setup_documents(self):
        """Setup test documents"""
        test_docs = [
            "A bond is a fixed-income security",
            "A stock represents ownership in a company",
            "A mutual fund pools money from investors",
            "Diversification reduces portfolio risk",
            "Asset allocation is key to long-term success"
        ]
        store.documents = test_docs
        store.add_documents(test_docs)
        yield
        store.documents = []

    def test_tfidf_retriever_initialization(self):
        """Test TFIDFRetriever can be initialized"""
        retriever = TFIDFRetriever()
        assert retriever is not None

    def test_tfidf_retriever_retrieve(self):
        """Test TFIDFRetriever retrieval"""
        retriever = TFIDFRetriever()
        results = retriever.retrieve("What is a stock?", k=2)
        
        assert isinstance(results, list)
        assert all(isinstance(r, RetrievalResult) for r in results)
        assert all(r.source == "tfidf" for r in results)

    def test_tfidf_retriever_scoring(self):
        """Test TFIDFRetriever returns scores"""
        retriever = TFIDFRetriever()
        results = retriever.retrieve("stock company ownership", k=3)
        
        assert len(results) > 0
        assert all(hasattr(r, 'similarity_score') for r in results)
        assert all(r.similarity_score >= 0 for r in results)


class TestSemanticRetriever:
    """Test Semantic Retriever"""

    @pytest.fixture(autouse=True)
    def setup_documents(self):
        """Setup test documents"""
        test_docs = [
            "A bond is a fixed-income security",
            "A stock represents ownership in a company",
            "A mutual fund pools money from investors",
            "Diversification reduces portfolio risk",
            "Asset allocation is key to long-term success"
        ]
        store.documents = test_docs
        store.add_documents(test_docs)
        yield
        store.documents = []

    def test_semantic_retriever_initialization(self):
        """Test SemanticRetriever can be initialized"""
        retriever = SemanticRetriever()
        assert retriever is not None

    def test_semantic_retriever_retrieve(self):
        """Test SemanticRetriever retrieval"""
        retriever = SemanticRetriever()
        results = retriever.retrieve("equity investments", k=2)
        
        assert isinstance(results, list)
        if len(results) > 0:
            assert all(isinstance(r, RetrievalResult) for r in results)
            assert all(r.source == "semantic" for r in results)

    def test_semantic_retriever_with_empty_documents(self):
        """Test SemanticRetriever with no documents"""
        retriever = SemanticRetriever()
        store.semantic_embeddings = None
        
        results = retriever.retrieve("test", k=2)
        assert isinstance(results, list)


class TestGetRetriever:
    """Test get_retriever factory function"""

    @pytest.fixture(autouse=True)
    def setup_documents(self):
        """Setup test documents"""
        test_docs = [
            "A bond is a fixed-income security",
            "A stock represents ownership in a company",
            "A mutual fund pools money from investors",
        ]
        store.documents = test_docs
        store.add_documents(test_docs)
        yield
        store.documents = []

    def test_get_retriever_default_hybrid(self):
        """Test get_retriever returns HybridRetriever by default"""
        retriever = get_retriever()
        assert isinstance(retriever, HybridRetriever)

    def test_get_retriever_hybrid_mode(self):
        """Test get_retriever with explicit hybrid mode"""
        retriever = get_retriever(mode="hybrid")
        assert isinstance(retriever, HybridRetriever)

    def test_get_retriever_tfidf_mode(self):
        """Test get_retriever with tfidf mode"""
        retriever = get_retriever(mode="tfidf")
        assert isinstance(retriever, TFIDFRetriever)

    def test_get_retriever_semantic_mode(self):
        """Test get_retriever with semantic mode"""
        retriever = get_retriever(mode="semantic")
        assert isinstance(retriever, SemanticRetriever)

    def test_get_retriever_caches_default(self):
        """Test get_retriever caches the default retriever"""
        r1 = get_retriever("hybrid")
        r2 = get_retriever("hybrid")
        # Should be the same instance (singleton for hybrid)
        assert r1 is r2


class TestQueryRAGWithScores:
    """Test query_rag_with_scores convenience function"""

    @pytest.fixture(autouse=True)
    def setup_documents(self):
        """Setup test documents"""
        test_docs = [
            "A bond is a fixed-income security where you lend money",
            "A stock represents ownership in a company and potential dividends",
            "A mutual fund pools money from many investors",
            "Diversification across asset classes reduces risk",
            "Asset allocation is the key to long-term investment success"
        ]
        store.documents = test_docs
        store.add_documents(test_docs)
        yield
        store.documents = []

    def test_query_rag_with_scores_hybrid(self):
        """Test query_rag_with_scores with hybrid mode"""
        results = query_rag_with_scores("What are bonds?", k=2, mode="hybrid")
        
        assert isinstance(results, list)
        assert all("document" in r for r in results)
        assert all("similarity_score" in r for r in results)
        assert all("index" in r for r in results)
        assert all("source" in r for r in results)

    def test_query_rag_with_scores_tfidf(self):
        """Test query_rag_with_scores with tfidf mode"""
        results = query_rag_with_scores("stock ownership company", k=2, mode="tfidf")
        
        assert isinstance(results, list)
        if len(results) > 0:
            assert all(r["source"] == "tfidf" for r in results)

    def test_query_rag_with_scores_semantic(self):
        """Test query_rag_with_scores with semantic mode"""
        results = query_rag_with_scores("investment pool fund", k=2, mode="semantic")
        
        assert isinstance(results, list)
        if len(results) > 0:
            assert all(r["source"] == "semantic" for r in results)

    def test_query_rag_with_scores_returns_documents(self):
        """Test that results contain actual documents"""
        results = query_rag_with_scores("diversification asset allocation", k=3)
        
        assert len(results) > 0
        for result in results:
            assert isinstance(result["document"], str)
            assert len(result["document"]) > 0

    def test_query_rag_with_scores_similarity_range(self):
        """Test similarity scores are in valid range"""
        results = query_rag_with_scores("bonds", k=3)
        
        for result in results:
            assert 0 <= result["similarity_score"] <= 1, \
                f"Similarity score {result['similarity_score']} out of range"

    def test_query_rag_with_scores_sorted(self):
        """Test results are sorted by similarity (descending)"""
        results = query_rag_with_scores("bonds mutual funds stocks", k=3)
        
        scores = [r["similarity_score"] for r in results]
        assert scores == sorted(scores, reverse=True)


class TestRetrieverBackendSwitching:
    """Test switching between retriever backends"""

    @pytest.fixture(autouse=True)
    def setup_documents(self):
        """Setup test documents"""
        test_docs = [
            "Risk management is critical for portfolio protection",
            "Rebalancing helps maintain target asset allocation",
            "Dollar cost averaging reduces market timing risk",
            "Emergency funds should cover 3-6 months of expenses",
        ]
        store.documents = test_docs
        store.add_documents(test_docs)
        yield
        store.documents = []

    def test_all_backends_return_results(self):
        """Test all backends return results for same query"""
        query = "What is risk management?"
        
        hybrid_results = get_retriever("hybrid").retrieve(query, k=2)
        tfidf_results = get_retriever("tfidf").retrieve(query, k=2)
        semantic_results = get_retriever("semantic").retrieve(query, k=2)
        
        assert len(hybrid_results) > 0
        assert len(tfidf_results) > 0
        # Semantic may be empty if model not available
        assert isinstance(semantic_results, list)

    def test_different_backends_may_rank_differently(self):
        """Test that different backends might rank results differently"""
        query = "emergency fund expenses"
        
        hybrid_results = query_rag_with_scores(query, k=3, mode="hybrid")
        tfidf_results = query_rag_with_scores(query, k=3, mode="tfidf")
        
        # They might return different top results due to different scoring
        if len(hybrid_results) > 0 and len(tfidf_results) > 0:
            # Just verify we get results; exact ranking may differ
            assert len(hybrid_results) == len(tfidf_results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
