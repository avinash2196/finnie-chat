import time
import json
from types import SimpleNamespace
from fastapi.testclient import TestClient
import pytest

from app.main import app, _quote_agg_cache

client = TestClient(app)

class DummyClient:
    def __init__(self, mapping):
        self._mapping = mapping
    def get_quotes(self, symbols):
        # return objects with .price and .change_pct attributes
        out = {}
        for s in symbols:
            k = s.upper()
            v = self._mapping.get(k)
            if v is not None:
                out[k] = SimpleNamespace(price=v.get("price"), change_pct=v.get("change_pct"))
        return out


def test_market_quote_cache_miss_and_store(monkeypatch):
    # Ensure in-memory cache empty and no redis
    _quote_agg_cache.clear()
    monkeypatch.setattr("app.main._redis_client", None)

    dummy = DummyClient({"AAPL": {"price": 150.0, "change_pct": 1.2}})
    monkeypatch.setattr("app.main.get_client", lambda: dummy)

    resp = client.post("/market/quote", json={"symbols": ["AAPL"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "quotes" in body
    assert "AAPL" in body["quotes"]
    assert body["quotes"]["AAPL"]["price"] == 150.0

    # aggregation cache must contain the normalized tuple key
    key = tuple(sorted(["AAPL"]))
    assert key in _quote_agg_cache
    assert _quote_agg_cache[key]["resp"]["quotes"]["AAPL"]["price"] == 150.0


def test_market_quote_cache_hit(monkeypatch):
    # Pre-populate cache with a known response and ensure get_client isn't called
    key = tuple(sorted(["MSFT"]))
    cached_resp = {"quotes": {"MSFT": {"price": 250.0, "change_pct": 0.5}}, "count": 1}
    _quote_agg_cache.clear()
    _quote_agg_cache[key] = {"ts": time.time(), "resp": cached_resp}

    def fail_if_called():
        raise AssertionError("get_client should not be called when cache hit")

    monkeypatch.setattr("app.main.get_client", lambda: SimpleNamespace(get_quotes=fail_if_called))
    monkeypatch.setattr("app.main._redis_client", None)

    resp = client.post("/market/quote", json={"symbols": ["MSFT"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body == cached_resp


def test_market_quote_error_from_client(monkeypatch):
    # Simulate client.get_quotes raising an exception
    _quote_agg_cache.clear()
    class BrokenClient:
        def get_quotes(self, symbols):
            raise RuntimeError("upstream failure")
    monkeypatch.setattr("app.main.get_client", lambda: BrokenClient())
    monkeypatch.setattr("app.main._redis_client", None)

    resp = client.post("/market/quote", json={"symbols": ["FAIL"]})
    assert resp.status_code == 200
    body = resp.json()
    # main returns an error dict with quotes empty on exception
    assert "error" in body
    assert body.get("quotes") == {}


def test_market_quote_uses_redis_when_present(monkeypatch):
    # Fake redis client that returns JSON bytes
    class FakeRedis:
        def __init__(self, val_bytes):
            self._val = val_bytes
        def get(self, key):
            return self._val
    cached_payload = {"quotes": {"SPY": {"price": 400.0, "change_pct": -0.5}}, "count": 1}
    fake = FakeRedis(json.dumps(cached_payload).encode("utf-8"))
    monkeypatch.setattr("app.main._redis_client", fake)

    # Ensure get_client would fail if invoked
    monkeypatch.setattr("app.main.get_client", lambda: (_ for _ in ()).throw(AssertionError("should not be called")))

    resp = client.post("/market/quote", json={"symbols": ["SPY"]})
    assert resp.status_code == 200
    assert resp.json() == cached_payload
