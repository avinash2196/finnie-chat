from app.rag.store import query_rag

def run(query: str):
    docs = query_rag(query)

    if not docs or len(docs) == 0:
        return None   # IMPORTANT

    explanation = "\n".join(docs)

    return (
        "Use ONLY the following trusted information:\n\n"
        + explanation
    )
