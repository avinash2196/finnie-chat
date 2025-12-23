import types
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient

from app import main as app_main


@pytest.fixture
def client():
    return TestClient(app_main.app)


def test_get_market_quote_success(monkeypatch, client):
    # Mock get_client().get_quotes to return a simple mapping
    class DummyClient:
        def get_quotes(self, symbols):
            return {s.upper(): SimpleNamespace(price=150.0, change_pct=1.23) for s in symbols}

    monkeypatch.setattr(app_main, "get_client", lambda: DummyClient())

    resp = client.post("/market/quote", json={"symbols": ["AAPL"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "quotes" in data
    assert data["quotes"]["AAPL"]["price"] == 150.0
    assert data["count"] == 1


def test_get_market_quote_aggregation_cache_hit(monkeypatch, client):
    # First call: return value and populate cache
    class FirstClient:
        def get_quotes(self, symbols):
            return {s.upper(): SimpleNamespace(price=200.0, change_pct=2.0) for s in symbols}

    monkeypatch.setattr(app_main, "get_client", lambda: FirstClient())
    r1 = client.post("/market/quote", json={"symbols": ["MSFT"]})
    assert r1.status_code == 200
    j1 = r1.json()
    assert j1["quotes"]["MSFT"]["price"] == 200.0

    # Now replace client with one that would raise if called; cached response should be served
    class BrokenClient:
        def get_quotes(self, symbols):
            raise RuntimeError("should not be called when cache hit")

    monkeypatch.setattr(app_main, "get_client", lambda: BrokenClient())
    r2 = client.post("/market/quote", json={"symbols": ["MSFT"]})
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2["quotes"]["MSFT"]["price"] == 200.0


def test_get_market_movers_handles_none(monkeypatch, client):
    # If get_market_data returns None for all symbols, movers should be empty
    def none_market_data(sym):
        return None

    monkeypatch.setattr(app_main, "get_market_data", none_market_data)
    resp = client.post("/market/movers", json={})
    assert resp.status_code == 200
    j = resp.json()
    assert "top_gainers" in j and isinstance(j["top_gainers"], list)
    assert j["count"] == 0


def test_get_market_movers_with_data(monkeypatch, client):
    # Provide synthetic market data for a small set of symbols
    def fake_market_data(sym):
        mapping = {
            "NVDA": {"price": 400.0, "change_pct": 10.0},
            "AAPL": {"price": 150.0, "change_pct": -2.0},
            "MSFT": {"price": 300.0, "change_pct": 1.5},
        }
        return mapping.get(sym, {"price": 100.0, "change_pct": 0.0})

    monkeypatch.setattr(app_main, "get_market_data", fake_market_data)
    resp = client.post("/market/movers", json={"symbols": ["NVDA", "AAPL", "MSFT"]})
    assert resp.status_code == 200
    j = resp.json()
    # NVDA should be among top gainers
    assert any(item["ticker"] == "NVDA" for item in j.get("top_gainers", []))
    assert j.get("count", 0) >= 3
