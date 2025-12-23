from fastapi.testclient import TestClient
import time
import json
from types import SimpleNamespace

from app.main import app, _quote_agg_cache

client = TestClient(app)


def test_market_movers_handles_missing_data(monkeypatch):
    # simulate get_market_data returning data for AAPL and None for FAKE
    def fake_get_market_data(sym):
        if sym == "AAPL":
            return {"price": 100.0, "change_pct": 5.0, "change": 5.0}
        return None
    monkeypatch.setattr("app.main.get_market_data", fake_get_market_data)

    resp = client.post("/market/movers", json={"symbols": ["AAPL", "FAKE"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "top_gainers" in body and "top_losers" in body
    assert body["count"] == 1
    assert any(g["ticker"] == "AAPL" for g in body["top_gainers"]) or len(body["top_gainers"]) == 1


def test_market_sectors_returns_etf_prices(monkeypatch):
    def fake_get_market_data(sym):
        # return simple dict for ETFs
        return {"price": 150.0, "change_pct": 1.2}
    monkeypatch.setattr("app.main.get_market_data", fake_get_market_data)

    resp = client.post("/market/sectors", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert "sectors" in body
    assert len(body["sectors"]) > 0
    assert all("price" in s for s in body["sectors"]) 


def test_market_screen_unknown_type():
    resp = client.post("/market/screen", json={"screener_type": "unknown", "params": {}})
    assert resp.status_code == 200
    body = resp.json()
    assert "error" in body and body["error"] == "Unknown screener type"


def test_market_quote_redis_setex_failure_falls_back(monkeypatch):
    _quote_agg_cache.clear()
    # fake redis that returns None on get and raises on setex
    class FakeRedis:
        def get(self, k):
            return None
        def setex(self, k, ttl, val):
            raise RuntimeError("redis write failed")
    monkeypatch.setattr("app.main._redis_client", FakeRedis())

    # dummy client
    class DummyClient:
        def get_quotes(self, syms):
            return {s.upper(): SimpleNamespace(price=123.0, change_pct=0.1) for s in syms}
    monkeypatch.setattr("app.main.get_client", lambda: DummyClient())

    resp = client.post("/market/quote", json={"symbols": ["SPY"]})
    assert resp.status_code == 200
    body = resp.json()
    # ensure fallback in-memory cache stored value
    key = tuple(sorted(["SPY"]))
    assert key in _quote_agg_cache
    assert _quote_agg_cache[key]["resp"]["quotes"]["SPY"]["price"] == 123.0


def test_market_quote_empty_symbols(monkeypatch):
    _quote_agg_cache.clear()
    class DummyClientEmpty:
        def get_quotes(self, syms):
            return {}
    monkeypatch.setattr("app.main.get_client", lambda: DummyClientEmpty())
    monkeypatch.setattr("app.main._redis_client", None)

    resp = client.post("/market/quote", json={"symbols": []})
    assert resp.status_code == 200
    body = resp.json()
    assert body["quotes"] == {}
    assert body["count"] == 0
