"""
Manual/integration tests that hit the running FastAPI server (localhost:8000).
Skipped by default; set RUN_MANUAL_TESTS=1 to enable.
"""
import os
import pytest
from fastapi.testclient import TestClient

from app.main import app


pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_MANUAL_TESTS"),
    reason="Manual integration tests require RUN_MANUAL_TESTS=1 and a running API server.",
)

# Use in-process TestClient so these tests run without a live server.
client = TestClient(app)
USER_ID = os.getenv("API_USER_ID", "user_001")


def test_portfolio_analytics_manual():
    resp = client.get(f"/users/{USER_ID}/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_value" in data


def test_performance_history_manual():
    resp = client.get(f"/users/{USER_ID}/performance?days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert "snapshots" in data


def test_market_quote_manual():
    symbols = ["AAPL", "MSFT", "GOOGL"]
    resp = client.post("/market/quote", json={"symbols": symbols})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("count", 0) >= 0


def test_screeners_manual():
    for screener_type in ["dividend", "growth", "value"]:
        resp = client.post(
            "/market/screen",
            json={"screener_type": screener_type, "params": {"user_id": USER_ID}},
        )
        assert resp.status_code == 200


def test_strategy_ideas_manual():
    resp = client.get("/strategy/ideas?risk_level=LOW")
    assert resp.status_code == 200


def test_price_sync_manual():
    resp = client.post(f"/users/{USER_ID}/sync/prices")
    assert resp.status_code == 200
