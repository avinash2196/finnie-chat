def test_rag_grounded_answer():
    output = chat_system("What is a stock?")
    assert "ownership" in output.lower()
def test_rag_missing_safe_fail():
    output = chat_system("Explain gamma squeeze mechanics")
    assert "don’t have enough" in output.lower()
def test_no_market_data_for_concept():
    output = chat_system("What is an ETF?")
    assert "USD" not in output
