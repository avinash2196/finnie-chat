"""
RAG Verification System - Track whether answers come from trusted RAG sources
This module adds transparency to responses by tracking source attribution
"""

def query_rag_with_scores(query, k=3, mode="hybrid"):
    """
    Query RAG and return documents WITH similarity scores.
    Uses retriever abstraction for flexible backend switching.
    
    Args:
        query: Query string
        k: Number of results to return
        mode: Retrieval mode ("hybrid", "tfidf", "semantic")
    
    Returns:
        List of dicts with document, similarity_score, index, source
    """
    from app.rag.retriever import query_rag_with_scores as retriever_query
    return retriever_query(query, k=k, mode=mode)


def categorize_answer_source(rag_results, answer):
    """
    Categorize whether an answer is:
    1. RAG_GROUNDED: Answer matches RAG documents (high confidence)
    2. RAG_INFORMED: Answer uses RAG but with some generalization
    3. LLM_GENERATED: Answer is LLM hallucination (no RAG match)
    
    Returns: (category, confidence, sources)
    """
    
    if not rag_results:
        return {
            "category": "LLM_GENERATED",
            "confidence": 0.0,
            "sources": [],
            "warning": "⚠️ No RAG documents found. Answer may be hallucinated.",
            "recommendation": "Use with caution - verify independently"
        }
    
    # Check if answer contains key terms from RAG documents
    rag_text = " ".join([r["document"].lower() for r in rag_results])
    answer_lower = answer.lower()
    
    # Extract key terms from RAG documents
    rag_keywords = set(rag_text.split())
    answer_keywords = set(answer_lower.split())
    
    # Calculate overlap
    overlap = len(rag_keywords & answer_keywords) / max(len(answer_keywords), 1)
    avg_similarity = sum(r["similarity_score"] for r in rag_results) / len(rag_results)
    
    # IMPROVED THRESHOLDS - More realistic for TF-IDF
    # TF-IDF typically gives lower scores (0.2-0.6) than semantic embeddings
    if avg_similarity > 0.5 and overlap > 0.25:
        # High match: similarity > 0.5 and good overlap
        category = "RAG_GROUNDED"
        confidence = 0.90
        warning = "✅ High confidence - Answer grounded in trusted RAG sources"
    elif avg_similarity > 0.35 and overlap > 0.15:
        # Medium match: some similarity and reasonable overlap
        category = "RAG_INFORMED"
        confidence = 0.70
        warning = "🟡 Medium confidence - Answer based on RAG but with LLM interpretation"
    elif avg_similarity > 0.20 and overlap > 0.10:
        # Low match: minimal similarity but some keywords match
        category = "RAG_PARTIALLY_MATCHED"
        confidence = 0.50
        warning = "🟡 Low-Medium confidence - Partial RAG match, some LLM generation"
    else:
        # No meaningful match
        category = "LLM_GENERATED"
        confidence = 0.3
        warning = "⚠️ Low confidence - Answer may not be grounded in RAG sources"
    
    return {
        "category": category,
        "confidence": confidence,
        "sources": rag_results,
        "overlap_percentage": round(overlap * 100, 1),
        "avg_similarity_score": round(avg_similarity, 3),
        "warning": warning,
        "recommendation": get_recommendation(category)
    }


def get_recommendation(category):
    """Get user recommendation based on source category"""
    recommendations = {
        "RAG_GROUNDED": "✅ Trust this answer - it's from verified financial knowledge",
        "RAG_INFORMED": "🟡 Answer is based on trusted sources but includes interpretation. Verify for important decisions.",
        "RAG_PARTIALLY_MATCHED": "🟡 Answer is partially grounded in trusted sources. Consider additional research.",
        "LLM_GENERATED": "⚠️ Answer is not from verified sources. Independently verify before using for decisions."
    }
    return recommendations.get(category, "Unknown")


def format_answer_with_sources(answer, verification_data):
    """
    Format answer for display with source attribution and warnings
    """
    from datetime import datetime
    
    formatted = f"""
{answer}

---

📊 **ANSWER VERIFICATION**
- **Source Type:** {verification_data['category']}
- **Confidence:** {verification_data['confidence']*100:.0f}%
- **Status:** {verification_data['warning']}

"""
    
    if verification_data['sources']:
        formatted += f"**RAG Match Score:** {verification_data['avg_similarity_score']}\n\n"
        formatted += "**Supporting Sources:**\n"
        for i, source in enumerate(verification_data['sources'], 1):
            doc_preview = source['document'][:100].replace('\n', ' ') + "..."
            formatted += f"{i}. _{doc_preview}_\n"
            formatted += f"   (Similarity: {source['similarity_score']:.2%})\n\n"
    
    formatted += f"**Recommendation:** {verification_data['recommendation']}\n"
    formatted += f"_Verified at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
    
    return formatted
