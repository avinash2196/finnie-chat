from app.rag.store import query_rag
from app.rag.verification import query_rag_with_scores, categorize_answer_source

def run(query: str, return_verification=False):
    """
    Run educator agent with optional answer verification
    
    Args:
        query: User question
        return_verification: If True, return verification data with answer
    
    Returns:
        answer (str) or (answer, verification_data) tuple
    """
    docs = query_rag(query)

    if not docs or len(docs) == 0:
        return None   # IMPORTANT

    explanation = "\n".join(docs)

    answer = (
        "Use ONLY the following trusted information:\n\n"
        + explanation
    )
    
    if return_verification:
        # Get scores for verification
        rag_with_scores = query_rag_with_scores(query)
        verification = categorize_answer_source(rag_with_scores, answer)
        return answer, verification
    
    return answer
