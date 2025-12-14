def test_no_disclaimer_for_low_risk():
    output = chat_system("What is a stock?")
    assert "financial advice" not in output.lower()

def test_disclaimer_for_med_risk():
    output = chat_system("Is ETF safer than stocks?")
    assert "financial advice" in output.lower()
