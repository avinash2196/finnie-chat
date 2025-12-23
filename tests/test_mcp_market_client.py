import time
from types import SimpleNamespace
import pytest

from app.mcp import market as market_client_module


def test_market_client_get_quote_uses_cache(monkeypatch):
    # Dummy server that records calls
    class DummyServer:
        def __init__(self):
            self.calls = []

        def call_tool(self, name, args):
            self.calls.append((name, args))
            if name == "get_quote":
                return {"ticker": args["ticker"].upper(), "price": 50.0, "currency": "USD", "change_pct": 0.5}
            raise RuntimeError("unexpected")

    dummy = DummyServer()
    monkeypatch.setattr(market_client_module, "get_market_server", lambda: dummy)

    client = market_client_module.MarketClient(ttl_seconds=2)
    q1 = client.get_quote("abc")
    assert q1.price == 50.0
    # second call should hit cache and not call server again
    q2 = client.get_quote("ABC")
    assert q2.price == 50.0
    assert len(dummy.calls) == 1


def test_market_client_get_quotes_batch_failure(monkeypatch):
    class BrokenServer:
        def call_tool(self, name, args):
            if name == "get_quotes":
                raise RuntimeError("batch fail")
            return {}

    monkeypatch.setattr(market_client_module, "get_market_server", lambda: BrokenServer())
    client = market_client_module.MarketClient(ttl_seconds=1)
    out = client.get_quotes(["X1", "X2"])
    assert isinstance(out, dict)
    assert out["X1"].price is None and out["X1"].error is not None
