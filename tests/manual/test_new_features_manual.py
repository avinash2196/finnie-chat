"""
Manual/integration tests that hit the running FastAPI server (localhost:8000).
Skipped by default; set RUN_MANUAL_TESTS=1 to enable.
"""
import os
import requests
import pytest


pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_MANUAL_TESTS"),
    reason="Manual integration tests require RUN_MANUAL_TESTS=1 and a running API server.",
)


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
USER_ID = os.getenv("API_USER_ID", "user_001")


def test_portfolio_analytics_manual():
    url = f"{API_BASE_URL}/users/{USER_ID}/analytics"
    resp = requests.get(url, timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_value" in data


def test_performance_history_manual():
    url = f"{API_BASE_URL}/users/{USER_ID}/performance?days=30"
    resp = requests.get(url, timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert "snapshots" in data


def test_market_quote_manual():
    url = f"{API_BASE_URL}/market/quote"
    symbols = ["AAPL", "MSFT", "GOOGL"]
    resp = requests.post(url, json={"symbols": symbols}, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("count", 0) >= 0


def test_screeners_manual():
    url = f"{API_BASE_URL}/market/screen"
    for screener_type in ["dividend", "growth", "value"]:
        resp = requests.post(url, json={"screener_type": screener_type, "params": {"user_id": USER_ID}}, timeout=15)
        assert resp.status_code == 200


def test_strategy_ideas_manual():
    url = f"{API_BASE_URL}/strategy/ideas?risk_level=LOW"
    resp = requests.get(url, timeout=5)
    assert resp.status_code == 200


def test_price_sync_manual():
    url = f"{API_BASE_URL}/users/{USER_ID}/sync/prices"
    resp = requests.post(url, timeout=15)
    assert resp.status_code == 200
