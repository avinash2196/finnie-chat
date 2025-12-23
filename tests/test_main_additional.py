import time
from types import SimpleNamespace
import json

import pytest
from fastapi.testclient import TestClient

from app import main as app_main


def test_http_timing_middleware_adds_header():
    client = TestClient(app_main.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    # header should exist and be an integer string
    assert "X-Process-Time-ms" in resp.headers
    assert resp.headers["X-Process-Time-ms"].isdigit()


def test_timed_external_call_decorator_reports_metric(monkeypatch):
    calls = []

    def fake_track_metric(name, value, props=None):
        calls.append((name, value, props))

    monkeypatch.setattr(app_main.observability, "track_metric", fake_track_metric)

    @app_main.timed_external_call("external_test")
    def slow_add(a, b):
        time.sleep(0.01)
        return a + b

    res = slow_add(2, 3)
    assert res == 5
    assert any("external_test" in c[2].get("call", "external_test") if c[2] else True or "external_test" in c[0] for c in calls)


def test_market_quote_redis_path(monkeypatch):
    # Simulate redis client returning a cached JSON
    cached = {"quotes": {"AAPL": {"price": 9.99}}, "count": 1}

    class FakeRedis:
        def __init__(self):
            self.store = {}

        def get(self, k):
            return json.dumps(cached).encode()

    monkeypatch.setattr(app_main, "_redis_client", FakeRedis())

    client = TestClient(app_main.app)
    resp = client.post("/market/quote", json={"symbols": ["AAPL"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("quotes", {}).get("AAPL", {}).get("price") == 9.99
