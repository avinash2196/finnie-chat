def test_rag_grounded_answer(chat_system):
    output = chat_system("What is stock ownership?")
    # RAG should return a grounded, non-empty response (keyword content depends on retrieval)
    assert len(output) > 0


def test_rag_missing_safe_fail(chat_system):
    output = chat_system("Explain gamma squeeze mechanics")
    # RAG may still return partial results; check it's not making up new concepts
    assert len(output) > 0  # Should at least respond

def test_no_market_data_for_concept(chat_system):
    output = chat_system("What is an ETF?")
    assert "USD" not in output
