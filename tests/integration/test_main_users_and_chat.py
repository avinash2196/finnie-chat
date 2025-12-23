from fastapi.testclient import TestClient
import pytest
import os
from types import SimpleNamespace

from app.main import app, _quote_agg_cache

client = TestClient(app)


def test_user_crud_and_portfolio_flow():
    # create user
    resp = client.post("/users", json={"email": "u1@example.com", "username": "user_test", "risk_tolerance": "LOW"})
    assert resp.status_code == 200
    body = resp.json()
    if body.get("status") == "error":
        # User may already exist from previous runs; try to fetch by username
        get_resp = client.get(f"/users/user_test")
        assert get_resp.status_code == 200
        user_id = get_resp.json().get("user_id")
    else:
        assert body["status"] == "success"
        user_id = body["user_id"]

    # get user
    resp = client.get(f"/users/{user_id}")
    assert resp.status_code == 200
    got = resp.json()
    assert got["username"] == "user_test"

    # add holding
    resp = client.post(f"/users/{user_id}/holdings", json={"ticker": "ABC", "quantity": 10, "purchase_price": 2.0})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"

    # list holdings
    resp = client.get(f"/users/{user_id}/holdings")
    assert resp.status_code == 200
    j = resp.json()
    assert j["total_value"] >= 0

    # snapshot
    resp = client.post(f"/users/{user_id}/snapshot")
    assert resp.status_code == 200
    s = resp.json()
    assert s["status"] == "success"

    # allocation
    resp = client.get(f"/users/{user_id}/allocation")
    assert resp.status_code == 200
    alloc = resp.json()
    assert "allocation" in alloc

    # delete holding (non-existing id triggers error path)
    resp = client.delete(f"/users/{user_id}/holdings/not-a-real-id")
    assert resp.status_code == 200
    assert resp.json().get("status") == "error" or "error" in resp.json()


def test_get_portfolio_analytics_no_holdings(monkeypatch):
    # create a new user without holdings
    resp = client.post("/users", json={"email": "u2@example.com", "username": "user_empty", "risk_tolerance": "MEDIUM"})
    body = resp.json()
    if body.get("status") == "error":
        get_resp = client.get("/users/user_empty")
        assert get_resp.status_code == 200
        user_id = get_resp.json().get("user_id")
    else:
        user_id = body["user_id"]

    resp = client.get(f"/users/{user_id}/analytics")
    # with no holdings this should return error
    assert resp.status_code == 200
    j = resp.json()
    assert "error" in j or "total_value" in j


def test_chat_guardrail_and_exception(monkeypatch):
    # simulate input_guardrails blocking
    monkeypatch.setattr("app.main.input_guardrails", lambda msg: (False, "blocked message"))
    resp = client.post("/chat", json={"message": "bad", "user_id": "user_001"})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("reply") == "blocked message"

    # simulate exception in handle_message to exercise chat exception handling
    def fake_guard(msg):
        return True, msg
    monkeypatch.setattr("app.main.input_guardrails", fake_guard)
    def broken_handle_message(msg, conversation_context=None, user_id=None, root_run_id=None):
        raise RuntimeError("boom")
    monkeypatch.setattr("app.main.handle_message", broken_handle_message)

    with pytest.raises(RuntimeError):
        client.post("/chat", json={"message": "hi", "user_id": "user_001"})
