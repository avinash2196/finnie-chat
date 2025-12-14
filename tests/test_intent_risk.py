import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.intent import classify_intent

def test_intent_low_risk():
    """Test that educational questions are LOW risk"""
    intent, risk = classify_intent("What is a stock?")
    assert intent == "ASK_CONCEPT"
    assert risk == "LOW"

def test_intent_high_risk():
    """Test that buy/sell requests are HIGH risk"""
    intent, risk = classify_intent("Tell me what stock to buy")
    assert risk == "HIGH"

def test_intent_market_query():
    """Test that market queries are detected"""
    intent, risk = classify_intent("What is the price of AAPL today?")
    assert intent == "ASK_MARKET"
    assert risk == "LOW"
