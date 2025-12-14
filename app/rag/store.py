from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

# Simple TF-IDF based RAG (no PyTorch/sentence-transformers needed)
vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
documents = []
embeddings = None
store_path = "chroma/embeddings.pkl"

def add_documents(texts):
    global documents, embeddings, vectorizer
    documents = texts
    embeddings = vectorizer.fit_transform(texts)
    # Save to disk
    os.makedirs("chroma", exist_ok=True)
    with open(store_path, 'wb') as f:
        pickle.dump({'vectorizer': vectorizer, 'embeddings': embeddings, 'documents': documents}, f)

def load_documents():
    global documents, embeddings, vectorizer
    if os.path.exists(store_path):
        with open(store_path, 'rb') as f:
            data = pickle.load(f)
            vectorizer = data['vectorizer']
            embeddings = data['embeddings']
            documents = data['documents']

# Load on startup
load_documents()

def query_rag(query, k=3):
    global embeddings, vectorizer, documents
    if embeddings is None or len(documents) == 0:
        return ["No documents available. Please ingest documents first."]
    
    # Transform query using the fitted vectorizer
    query_vec = vectorizer.transform([query])
    # Compute similarity
    similarities = cosine_similarity(query_vec, embeddings)[0]
    # Get top k
    top_indices = similarities.argsort()[-k:][::-1]
    return [documents[i] for i in top_indices if i < len(documents)]
