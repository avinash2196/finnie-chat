import pytest
from types import SimpleNamespace

from app import observability as obs_mod


def test_guess_asset_type():
    o = obs_mod.observability
    assert o.guess_asset_type("BTC price") == "crypto"
    assert o.guess_asset_type("This is an ETF mention XLK") == "ETF"
    assert o.guess_asset_type("I like AAPL and MSFT") == "stock"
    res = o.guess_asset_type("something random")
    assert isinstance(res, str)


def test_track_agent_execution_decorator(monkeypatch):
    calls = {"events": [], "metrics": [], "exceptions": []}

    def fake_event(name, props=None):
        calls["events"].append((name, props))

    def fake_metric(name, value, props=None):
        calls["metrics"].append((name, value, props))

    def fake_exception(e, props=None):
        calls["exceptions"].append((e, props))

    monkeypatch.setattr(obs_mod.observability, "track_event", fake_event)
    monkeypatch.setattr(obs_mod.observability, "track_metric", fake_metric)
    monkeypatch.setattr(obs_mod.observability, "track_exception", fake_exception)

    @obs_mod.track_agent_execution("MyAgent")
    def succeed(x):
        return x * 2

    @obs_mod.track_agent_execution("MyAgent")
    def fail(x):
        raise ValueError("boom")

    assert succeed(3) == 6
    assert len(calls["events"]) >= 1
    assert any("success" in (p or {}).get("status", "") or p and p.get("status") == "success" for _, p in calls["events"]) or len(calls["metrics"]) >= 1

    with pytest.raises(ValueError):
        fail(1)
    assert len(calls["exceptions"]) >= 1


def test_track_llm_call_decorator(monkeypatch):
    calls = {"events": [], "metrics": [], "exceptions": []}

    def fake_event(name, props=None):
        calls["events"].append((name, props))

    def fake_metric(name, value, props=None):
        calls["metrics"].append((name, value, props))

    def fake_exception(e, props=None):
        calls["exceptions"].append((e, props))

    monkeypatch.setattr(obs_mod.observability, "track_event", fake_event)
    monkeypatch.setattr(obs_mod.observability, "track_metric", fake_metric)
    monkeypatch.setattr(obs_mod.observability, "track_exception", fake_exception)

    @obs_mod.track_llm_call("openai")
    def llm_success(prompt):
        return "ok"

    @obs_mod.track_llm_call("openai")
    def llm_fail(prompt):
        raise RuntimeError("fail")

    assert llm_success("hi") == "ok"
    assert len(calls["metrics"]) >= 1

    with pytest.raises(RuntimeError):
        llm_fail("hi")
    assert len(calls["exceptions"]) >= 1
