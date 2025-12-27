"""
Retriever abstraction layer for RAG systems.
Provides a unified interface for different retrieval backends (TF-IDF, semantic, hybrid).
"""

from typing import List, Dict, Optional, Protocol
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """Standard format for retrieval results."""
    document: str
    similarity_score: float
    index: int
    source: str = "unknown"  # e.g., "tfidf", "semantic", "hybrid"


class Retriever(Protocol):
    """Protocol for retrieval backends."""
    
    def retrieve(self, query: str, k: int = 3) -> List[RetrievalResult]:
        """Retrieve top-k documents for query."""
        ...


class HybridRetriever:
    """Hybrid retriever using TF-IDF + semantic search with score blending."""
    
    def __init__(self):
        from app.rag import store
        self._store = store
    
    def retrieve(self, query: str, k: int = 3) -> List[RetrievalResult]:
        """
        Retrieve using hybrid search (semantic + TF-IDF).
        Returns results with scores from the dominant method.
        """
        # Use the store's query_rag which already does hybrid search
        documents = self._store.query_rag(query, k=k)
        
        if not documents:
            return []
        
        # Get similarity scores from the underlying methods
        results = []
        
        # Try to get scores from TF-IDF (fallback scoring)
        if self._store.tfidf_embeddings is not None:
            from sklearn.metrics.pairwise import cosine_similarity
            query_vec = self._store.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self._store.tfidf_embeddings)[0]
            
            # Match returned documents to their indices
            for doc in documents:
                try:
                    idx = self._store.documents.index(doc)
                    score = float(similarities[idx])
                    results.append(RetrievalResult(
                        document=doc,
                        similarity_score=score,
                        index=idx,
                        source="hybrid"
                    ))
                except ValueError:
                    # Document not found in list (shouldn't happen)
                    results.append(RetrievalResult(
                        document=doc,
                        similarity_score=0.0,
                        index=-1,
                        source="hybrid"
                    ))
        else:
            # No scoring available, return documents with placeholder scores
            for i, doc in enumerate(documents):
                results.append(RetrievalResult(
                    document=doc,
                    similarity_score=0.0,
                    index=i,
                    source="hybrid"
                ))
        
        return results[:k]


class TFIDFRetriever:
    """Pure TF-IDF retriever."""
    
    def __init__(self):
        from app.rag import store
        self._store = store
    
    def retrieve(self, query: str, k: int = 3) -> List[RetrievalResult]:
        """Retrieve using TF-IDF only."""
        if self._store.tfidf_embeddings is None or len(self._store.documents) == 0:
            return []
        
        from sklearn.metrics.pairwise import cosine_similarity
        query_vec = self._store.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self._store.tfidf_embeddings)[0]
        
        top_indices = similarities.argsort()[-k:][::-1]
        
        results = []
        for idx in top_indices:
            if idx < len(self._store.documents):
                results.append(RetrievalResult(
                    document=self._store.documents[idx],
                    similarity_score=float(similarities[idx]),
                    index=int(idx),
                    source="tfidf"
                ))
        
        return results


class SemanticRetriever:
    """Pure semantic search retriever."""
    
    def __init__(self):
        from app.rag import store
        self._store = store
    
    def retrieve(self, query: str, k: int = 3) -> List[RetrievalResult]:
        """Retrieve using semantic embeddings only."""
        if self._store.semantic_embeddings is None or len(self._store.documents) == 0:
            return []
        
        self._store._ensure_model()
        if not self._store.semantic_model:
            return []
        
        import numpy as np
        query_vec = self._store.semantic_model.encode(
            [query], 
            normalize_embeddings=True, 
            show_progress_bar=False
        )[0]
        
        sims = np.dot(self._store.semantic_embeddings, query_vec)
        top_indices = np.argsort(sims)[-k:][::-1]
        
        results = []
        for idx in top_indices:
            if idx < len(self._store.documents):
                results.append(RetrievalResult(
                    document=self._store.documents[idx],
                    similarity_score=float(sims[idx]),
                    index=int(idx),
                    source="semantic"
                ))
        
        return results


# Singleton retrievers
_default_retriever: Optional[Retriever] = None


def get_retriever(mode: str = "hybrid") -> Retriever:
    """
    Get retriever instance.
    
    Args:
        mode: "hybrid" (default), "tfidf", or "semantic"
    
    Returns:
        Retriever instance
    """
    global _default_retriever
    
    if mode == "tfidf":
        return TFIDFRetriever()
    elif mode == "semantic":
        return SemanticRetriever()
    else:  # hybrid (default)
        if _default_retriever is None:
            _default_retriever = HybridRetriever()
        return _default_retriever


def query_rag_with_scores(query: str, k: int = 3, mode: str = "hybrid") -> List[Dict]:
    """
    Convenience function to query RAG and return results with scores.
    
    Args:
        query: Query string
        k: Number of results to return
        mode: Retrieval mode ("hybrid", "tfidf", "semantic")
    
    Returns:
        List of dicts with document, similarity_score, index, source
    """
    retriever = get_retriever(mode)
    results = retriever.retrieve(query, k=k)
    
    return [
        {
            "document": r.document,
            "similarity_score": r.similarity_score,
            "index": r.index,
            "source": r.source,
        }
        for r in results
    ]
