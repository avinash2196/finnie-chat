from app.intent import classify_intent


def test_intent_portfolio_keywords():
    intent, risk = classify_intent("Should I rebalance my allocation? My portfolio is concentrated")
    assert intent == "ASK_PORTFOLIO"
    assert risk == "MED"


def test_intent_risk_keywords():
    intent, risk = classify_intent("Is my portfolio volatility too high? How's my sharpe")
    assert intent == "ASK_RISK"
    assert risk == "MED"


def test_intent_strategy_keywords():
    intent, risk = classify_intent("Find growth and dividend stocks to screen")
    assert intent == "ASK_STRATEGY"
    assert risk == "MED"


def test_intent_other():
    intent, risk = classify_intent("Hello there")
    assert intent == "OTHER"
    assert risk == "LOW"
