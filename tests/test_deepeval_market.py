import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_market_quote_basic(client):
    """Basic smoke test for /market/quote endpoint using TestClient"""
    resp = client.post("/market/quote", json={"symbols": ["AAPL", "MSFT", "NVDA"]})
    assert resp.status_code == 200
    js = resp.json()
    assert "quotes" in js
    for t in ["AAPL", "MSFT", "NVDA"]:
        assert t in js.get("quotes", {})


def test_market_movers_shape(client):
    resp = client.post("/market/movers", json={})
    assert resp.status_code == 200
    js = resp.json()
    assert isinstance(js.get("top_gainers", []), list)
    assert isinstance(js.get("top_losers", []), list)


def test_market_sectors_shape(client):
    resp = client.post("/market/sectors")
    assert resp.status_code == 200
    js = resp.json()
    assert isinstance(js.get("sectors", []), list)
