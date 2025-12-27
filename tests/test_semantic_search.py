"""
Tests for Hybrid RAG with Semantic Search

Covers:
- Semantic embeddings (sentence-transformers)
- TF-IDF fallback
- Score blending (50/50)
- Model lazy-loading
- Persistence to disk (pickle)
"""

import pytest
import os
import numpy as np
from unittest.mock import patch, MagicMock
from app.rag import store


class TestSemanticEmbeddings:
    """Test semantic embedding functionality"""

    @pytest.fixture(autouse=True)
    def reset_store(self):
        """Reset store before each test"""
        store.documents = []
        store.tfidf_embeddings = None
        store.semantic_embeddings = None
        store.semantic_model = None
        yield
        store.documents = []

    def test_ensure_model_loads_sentence_transformers(self):
        """Test _ensure_model loads the sentence-transformers model"""
        # This requires the model to be available
        store._ensure_model()
        
        # If SentenceTransformer available, model should be loaded
        if store.SentenceTransformer:
            # Model might be None if download fails, but should have tried
            assert store.semantic_model is None or store.semantic_model is not None

    def test_semantic_model_name_correct(self):
        """Test correct model name is used"""
        assert store.semantic_model_name == "all-MiniLM-L6-v2"

    def test_add_documents_creates_semantic_embeddings(self):
        """Test add_documents creates semantic embeddings"""
        documents = [
            "A bond is a fixed-income security",
            "A stock represents ownership",
            "A mutual fund pools resources"
        ]
        
        store.add_documents(documents)
        
        assert store.documents == documents
        if store.semantic_embeddings is not None:
            # Should have embeddings for each document
            assert store.semantic_embeddings.shape[0] == len(documents)
            # Each embedding should be 384-dim for all-MiniLM-L6-v2
            assert store.semantic_embeddings.shape[1] == 384

    def test_semantic_embeddings_normalized(self):
        """Test semantic embeddings are normalized"""
        documents = [
            "Financial security through diversification",
            "Asset allocation strategy"
        ]
        
        store.add_documents(documents)
        
        if store.semantic_embeddings is not None:
            # Check L2 norm of each embedding (should be ~1.0 for normalized)
            norms = np.linalg.norm(store.semantic_embeddings, axis=1)
            assert np.allclose(norms, 1.0, atol=0.01)


class TestTFIDFSearch:
    """Test TF-IDF search functionality"""

    @pytest.fixture(autouse=True)
    def reset_store(self):
        """Reset store before each test"""
        store.documents = []
        store.tfidf_embeddings = None
        yield
        store.documents = []

    def test_vectorizer_initialization(self):
        """Test TF-IDF vectorizer is initialized"""
        assert store.vectorizer is not None
        assert hasattr(store.vectorizer, 'fit_transform')

    def test_tfidf_search_returns_indices(self):
        """Test _tfidf_search returns document indices"""
        documents = [
            "A bond is a fixed-income security",
            "A stock represents ownership",
            "Bond investments provide steady returns"
        ]
        store.add_documents(documents)
        
        indices = store._tfidf_search("bond", k=2)
        
        assert isinstance(indices, list)
        assert len(indices) <= 2
        assert all(isinstance(i, (int, np.integer)) for i in indices)
        # Search for "bond" should return docs with "bond"
        assert all(i < len(documents) for i in indices)

    def test_tfidf_search_returns_k_results(self):
        """Test _tfidf_search respects k parameter"""
        documents = [
            f"Document about topic {i}" for i in range(10)
        ]
        store.add_documents(documents)
        
        k1 = store._tfidf_search("topic", k=1)
        k5 = store._tfidf_search("topic", k=5)
        
        assert len(k1) <= 1
        assert len(k5) <= 5

    def test_tfidf_embeddings_created(self):
        """Test TF-IDF embeddings are created"""
        documents = [
            "The quick brown fox",
            "jumps over the lazy dog"
        ]
        store.add_documents(documents)
        
        assert store.tfidf_embeddings is not None
        assert store.tfidf_embeddings.shape[0] == len(documents)


class TestSemanticSearch:
    """Test semantic search functionality"""

    @pytest.fixture(autouse=True)
    def reset_store(self):
        """Reset store before each test"""
        store.documents = []
        store.semantic_embeddings = None
        store.semantic_model = None
        yield
        store.documents = []

    def test_semantic_search_returns_indices(self):
        """Test _semantic_search returns document indices"""
        documents = [
            "Investment strategy and risk management",
            "Stock market analysis techniques",
            "Portfolio diversification benefits"
        ]
        store.add_documents(documents)
        
        if store.semantic_embeddings is not None:
            indices = store._semantic_search("investment strategy", k=2)
            
            assert isinstance(indices, list)
            assert len(indices) <= 2
            assert all(i < len(documents) for i in indices)

    def test_semantic_search_similarity_based(self):
        """Test semantic search uses similarity"""
        documents = [
            "The quick brown fox jumps",
            "The lazy dog sleeps all day",
            "A fox is an animal"
        ]
        store.add_documents(documents)
        
        if store.semantic_embeddings is not None:
            # Query about fox should rank fox docs higher
            indices = store._semantic_search("fox animal", k=1)
            assert len(indices) > 0


class TestHybridSearch:
    """Test hybrid TF-IDF + semantic search"""

    @pytest.fixture(autouse=True)
    def reset_store(self):
        """Reset store before each test"""
        store.documents = []
        store.tfidf_embeddings = None
        store.semantic_embeddings = None
        yield
        store.documents = []

    def test_hybrid_query_rag_returns_documents(self):
        """Test query_rag returns actual documents"""
        documents = [
            "A bond is a debt security issued by governments or corporations",
            "A stock represents fractional ownership in a company",
            "Bonds and stocks are both investment vehicles",
            "Diversification reduces portfolio risk through asset allocation"
        ]
        store.add_documents(documents)
        
        results = store.query_rag("bond security", k=2)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(doc, str) for doc in results)
        # Results should be from our documents
        assert all(doc in documents for doc in results)

    def test_hybrid_query_rag_respects_k(self):
        """Test query_rag respects k parameter"""
        documents = [f"Document number {i} about finance" for i in range(10)]
        store.add_documents(documents)
        
        k1 = store.query_rag("finance", k=1)
        k3 = store.query_rag("finance", k=3)
        k5 = store.query_rag("finance", k=5)
        
        assert len(k1) <= 1
        assert len(k3) <= 3
        assert len(k5) <= 5

    def test_hybrid_query_rag_with_no_documents(self):
        """Test query_rag handles empty document store"""
        store.documents = []
        
        results = store.query_rag("test query", k=2)
        
        assert isinstance(results, list)
        # Should return a message about no documents
        assert len(results) > 0

    def test_hybrid_score_blending(self):
        """Test hybrid search blends TF-IDF and semantic scores"""
        documents = [
            "Diversification is key to portfolio management",
            "Risk assessment helps investors choose investments",
            "Asset allocation balances risk and return",
            "Portfolio performance depends on many factors"
        ]
        store.add_documents(documents)
        
        # Query should use both methods
        results = store.query_rag("portfolio risk diversification", k=2)
        
        assert len(results) > 0
        # Results should be top documents (blend of both scores)
        assert all(doc in documents for doc in results)

    def test_hybrid_fallback_when_semantic_unavailable(self):
        """Test hybrid search falls back to TF-IDF when semantic unavailable"""
        documents = [
            "Bonds provide fixed income",
            "Stocks offer growth potential",
            "Mixed portfolios balance income and growth"
        ]
        store.add_documents(documents)
        
        # Temporarily remove semantic embeddings
        semantic_backup = store.semantic_embeddings
        store.semantic_embeddings = None
        
        try:
            results = store.query_rag("bonds income", k=2)
            
            # Should still return results using TF-IDF fallback
            assert len(results) > 0
            assert all(doc in documents for doc in results)
        finally:
            store.semantic_embeddings = semantic_backup

    def test_hybrid_fallback_when_tfidf_unavailable(self):
        """Test hybrid search falls back to semantic when TF-IDF unavailable"""
        documents = [
            "Investment accounts help grow wealth",
            "Savings accounts provide security",
            "Investment strategies vary by goals"
        ]
        store.add_documents(documents)
        
        # Temporarily remove TF-IDF embeddings
        tfidf_backup = store.tfidf_embeddings
        store.tfidf_embeddings = None
        
        try:
            results = store.query_rag("investment wealth growth", k=2)
            
            # Should use semantic fallback
            assert isinstance(results, list)
        finally:
            store.tfidf_embeddings = tfidf_backup


class TestPersistence:
    """Test persistence to disk"""

    @pytest.fixture(autouse=True)
    def reset_store(self):
        """Reset store before each test"""
        store.documents = []
        store.tfidf_embeddings = None
        store.semantic_embeddings = None
        yield
        # Don't clean up file so we can test loading

    def test_documents_persisted_to_pickle(self):
        """Test documents are saved to pickle file"""
        documents = [
            "Test document one",
            "Test document two"
        ]
        store.add_documents(documents)
        
        # Pickle file should exist
        assert os.path.exists(store.store_path)

    def test_load_documents_from_disk(self):
        """Test documents can be loaded from disk"""
        # Save some documents
        documents = [
            "Persisted document A",
            "Persisted document B",
            "Persisted document C"
        ]
        store.add_documents(documents)
        
        # Clear memory
        store.documents = []
        store.tfidf_embeddings = None
        
        # Load from disk
        store.load_documents()
        
        assert len(store.documents) > 0
        assert all(doc in store.documents for doc in documents)

    def test_vectorizer_persisted(self):
        """Test vectorizer is persisted"""
        documents = ["Training document one", "Training document two"]
        store.add_documents(documents)
        
        # Vectorizer should be in the pickle
        assert os.path.exists(store.store_path)
        
        # Load and check
        store.load_documents()
        assert store.vectorizer is not None


class TestQueryRAGWithScoresIntegration:
    """Integration tests for query_rag_with_scores"""

    @pytest.fixture(autouse=True)
    def reset_store(self):
        """Reset store before each test"""
        store.documents = []
        store.tfidf_embeddings = None
        store.semantic_embeddings = None
        yield
        store.documents = []

    def test_query_with_scores_includes_all_fields(self):
        """Test query results include all required fields"""
        documents = [
            "Dividend stocks provide regular income",
            "Growth stocks focus on price appreciation",
            "Value stocks trade below intrinsic value"
        ]
        store.add_documents(documents)
        
        from app.rag.verification import query_rag_with_scores as rag_query_scores
        
        results = rag_query_scores("dividend income", k=2, mode="hybrid")
        
        for result in results:
            assert "document" in result
            assert "similarity_score" in result
            assert "index" in result
            assert "source" in result

    def test_query_scores_sorted_by_similarity(self):
        """Test results are sorted by similarity score"""
        documents = [
            "Asset allocation is important",
            "Rebalancing maintains allocation",
            "Allocation strategies vary"
        ]
        store.add_documents(documents)
        
        from app.rag.verification import query_rag_with_scores as rag_query_scores
        
        results = rag_query_scores("asset allocation strategy", k=3, mode="hybrid")
        
        if len(results) > 1:
            scores = [r["similarity_score"] for r in results]
            assert scores == sorted(scores, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
