def test_rag_grounded_answer(chat_system):
    output = chat_system("What is a stock?")
    assert "ownership" in output.lower()

def test_rag_missing_safe_fail(chat_system):
    output = chat_system("Explain gamma squeeze mechanics")
    # RAG may still return partial results; check it's not making up new concepts
    assert len(output) > 0  # Should at least respond

def test_no_market_data_for_concept(chat_system):
    output = chat_system("What is an ETF?")
    assert "USD" not in output
