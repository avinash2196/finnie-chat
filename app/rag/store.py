"""RAG store with hybrid TF-IDF + semantic search (sentence-transformers).

Falls back to TF-IDF if semantic model/embeddings are unavailable.
"""

import os
import pickle
import numpy as np
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None  # Model optional; TF-IDF will still work


# TF-IDF globals
vectorizer = TfidfVectorizer(stop_words='english', max_features=1024)
tfidf_embeddings = None

# Semantic globals
semantic_model_name = "all-MiniLM-L6-v2"
semantic_model = None
semantic_embeddings = None

documents: List[str] = []
store_path = "chroma/embeddings.pkl"


def _ensure_model():
    global semantic_model
    if semantic_model is None and SentenceTransformer:
        try:
            semantic_model = SentenceTransformer(semantic_model_name)
        except Exception:
            semantic_model = None


def add_documents(texts: List[str]):
    """Fit TF-IDF and semantic embeddings and persist to disk."""
    global documents, tfidf_embeddings, semantic_embeddings, vectorizer
    documents = texts

    # TF-IDF
    tfidf_embeddings = vectorizer.fit_transform(texts)

    # Semantic
    _ensure_model()
    if semantic_model:
        # Encode to numpy array, normalized
        embeds = semantic_model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        semantic_embeddings = np.array(embeds)
    else:
        semantic_embeddings = None

    # Save to disk
    os.makedirs("chroma", exist_ok=True)
    with open(store_path, 'wb') as f:
        pickle.dump({
            'vectorizer': vectorizer,
            'tfidf_embeddings': tfidf_embeddings,
            'semantic_embeddings': semantic_embeddings,
            'documents': documents,
            'semantic_model_name': semantic_model_name,
        }, f)


def load_documents():
    """Load embeddings and vectorizer from disk; lazy-load model when needed."""
    global documents, tfidf_embeddings, semantic_embeddings, vectorizer
    if os.path.exists(store_path):
        with open(store_path, 'rb') as f:
            data = pickle.load(f)
            vectorizer = data.get('vectorizer', vectorizer)
            tfidf_embeddings = data.get('tfidf_embeddings')
            semantic_embeddings = data.get('semantic_embeddings')
            documents = data.get('documents', [])


# Load on startup
load_documents()


def _semantic_search(query: str, k: int) -> List[int]:
    """Return indices ranked by semantic similarity."""
    if semantic_embeddings is None or len(documents) == 0:
        return []
    _ensure_model()
    if not semantic_model:
        return []
    query_vec = semantic_model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
    sims = np.dot(semantic_embeddings, query_vec)
    top_indices = np.argsort(sims)[-k:][::-1]
    return [int(i) for i in top_indices if i < len(documents)]


def _tfidf_search(query: str, k: int) -> List[int]:
    if tfidf_embeddings is None or len(documents) == 0:
        return []
    query_vec = vectorizer.transform([query])
    sims = cosine_similarity(query_vec, tfidf_embeddings)[0]
    top_indices = sims.argsort()[-k:][::-1]
    return [int(i) for i in top_indices if i < len(documents)]


def query_rag(query: str, k: int = 3) -> List[str]:
    """Hybrid search: semantic + TF-IDF with simple score blending."""
    if len(documents) == 0:
        return ["No documents available. Please ingest documents first."]

    # Get indices from each method
    tfidf_idx = _tfidf_search(query, k)
    semantic_idx = _semantic_search(query, k)

    # If only one method available, return that
    if semantic_idx and not tfidf_idx:
        return [documents[i] for i in semantic_idx][:k]
    if tfidf_idx and not semantic_idx:
        return [documents[i] for i in tfidf_idx][:k]

    # Blend scores when both available
    scores = {}
    # TF-IDF scores
    if tfidf_embeddings is not None:
        query_vec = vectorizer.transform([query])
        tfidf_sims = cosine_similarity(query_vec, tfidf_embeddings)[0]
        for i in tfidf_idx:
            scores[i] = scores.get(i, 0) + 0.5 * tfidf_sims[i]
    # Semantic scores
    if semantic_embeddings is not None and semantic_idx:
        _ensure_model()
        if semantic_model:
            qv = semantic_model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
            sem_sims = np.dot(semantic_embeddings, qv)
            for i in semantic_idx:
                scores[i] = scores.get(i, 0) + 0.5 * sem_sims[i]

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [documents[i] for i, _ in ranked[:k]] or [documents[i] for i in (semantic_idx or tfidf_idx)[:k]]
