"""
RAG Testing Script - Test improved RAG system with better knowledge base
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Fix encoding for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.rag.ingest import ingest
from app.rag.verification import query_rag_with_scores, categorize_answer_source

def test_rag_verification():
    """Test the improved RAG system"""
    
    print("="*70)
    print("RAG SYSTEM TESTING - Improved Knowledge Base")
    print("="*70)
    
    # Re-ingest with improved knowledge base
    print("\n[1] Ingesting improved knowledge base...")
    ingest()
    
    # Test queries
    test_queries = [
        "What is a stock?",
        "How do stocks work?",
        "What are bonds?",
        "Explain dividends",
        "What is a mutual fund?",
        "How does diversification reduce risk?",
        "What is the S&P 500?"
    ]
    
    print("\n[2] Testing RAG verification on financial concepts...\n")
    
    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"QUERY: {query}")
        print('='*70)
        
        # Get RAG results with scores
        rag_results = query_rag_with_scores(query, k=3)
        
        # Create a dummy answer for verification
        # (In real use, this would be the LLM-generated answer)
        dummy_answer = f"Answer about {query.lower()}"
        
        # Verify
        verification = categorize_answer_source(rag_results, dummy_answer)
        
        # Display results
        print(f"\nRAG Documents Found: {len(rag_results)}")
        print(f"Category: {verification['category']}")
        print(f"Confidence: {verification['confidence']*100:.0f}%")
        print(f"Average Similarity: {verification['avg_similarity_score']:.3f}")
        print(f"Keyword Overlap: {verification['overlap_percentage']:.1f}%")
        print(f"\nStatus: {verification['warning']}")
        print(f"Recommendation: {verification['recommendation']}")
        
        if rag_results:
            print("\nTop RAG Matches:")
            for i, source in enumerate(rag_results, 1):
                doc_preview = source['document'][:80].replace('\n', ' ') + "..."
                print(f"  {i}. [{source['similarity_score']:.3f}] {doc_preview}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_rag_verification()
