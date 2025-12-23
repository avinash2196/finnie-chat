"""Additional tests to increase coverage for main API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db, User, Holding, PortfolioSnapshot


@pytest.fixture
def test_db():
    """Create isolated in-memory DB and override dependency."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    return TestClient(app)


def _create_user(db, email="extra@test.com", username="extrauser"):
    user = User(email=email, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_metrics_endpoint(client):
    """Covers /metrics endpoint path."""
    with patch("app.main.get_gateway_metrics", return_value={"cache_hit_rate": 0.9, "failures": 0}):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "cache_hit_rate" in data


@patch("app.main.SyncTaskRunner.sync_now", return_value={"status": "success", "provider": "mock"})
def test_sync_portfolio_endpoint(mock_sync_now, client, test_db):
    db = test_db()
    user = _create_user(db, email="sync@test.com", username="syncuser")
    resp = client.post(f"/users/{user.id}/sync", json={"provider": "mock", "api_token": None})
    assert resp.status_code == 200
    assert resp.json().get("status") == "success"


@patch("app.main.SyncTaskRunner.sync_price_update", return_value={"status": "success", "updated": 3})
def test_sync_prices_endpoint(mock_sync, client, test_db):
    db = test_db()
    user = _create_user(db, email="prices@test.com", username="pricesuser")
    resp = client.post(f"/users/{user.id}/sync/prices")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "success"


def test_portfolio_analytics_with_holdings_and_snapshots(client, test_db):
    """Covers analytics calculations including snapshots-derived volatility/sharpe branches."""
    db = test_db()
    user = _create_user(db, email="analytics@test.com", username="analyticsuser")

    # Add holdings
    h1 = Holding(user_id=user.id, ticker="AAPL", quantity=10, purchase_price=150.0, current_price=160.0, total_value=1600.0, gain_loss=100.0)
    h2 = Holding(user_id=user.id, ticker="MSFT", quantity=5, purchase_price=300.0, current_price=310.0, total_value=1550.0, gain_loss=50.0)
    db.add_all([h1, h2])
    db.commit()

    # Add two snapshots to exercise returns path
    s1 = PortfolioSnapshot(user_id=user.id, total_value=3150.0)
    s2 = PortfolioSnapshot(user_id=user.id, total_value=3100.0)
    db.add_all([s1, s2])
    db.commit()

    resp = client.get(f"/users/{user.id}/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["holdings_count"] == 2
    # Ensure analytics fields exist
    for key in ["volatility", "sharpe_ratio", "diversification_score", "return_pct"]:
        assert key in data


def test_performance_history_endpoint(client, test_db):
    """Covers /users/{id}/performance endpoint."""
    db = test_db()
    user = _create_user(db, email="perf@test.com", username="perfuser")
    s1 = PortfolioSnapshot(user_id=user.id, total_value=1000.0)
    s2 = PortfolioSnapshot(user_id=user.id, total_value=1100.0)
    db.add_all([s1, s2])
    db.commit()

    resp = client.get(f"/users/{user.id}/performance?days=365")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 2


def test_verify_rag_endpoint_truncation(client):
    """Covers /verify-rag endpoint and document truncation branch."""
    long_text = "X" * 300
    fake_results = [
        {"document": long_text, "similarity_score": 0.9},
        {"document": "short", "similarity_score": 0.5},
    ]
    with patch("app.main.query_rag_with_scores", return_value=fake_results):
        with patch("app.main.categorize_answer_source", return_value={"category": "RAG_GROUNDED", "confidence": 0.95, "warning": None, "recommendation": "Use RAG"}):
            resp = client.post("/verify-rag", params={"query": "What is SCHD?"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["rag_documents_found"] == 2
            # First doc should be truncated in preview
            assert data["documents"][0]["text"].endswith("...")


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_strategy_ideas_endpoint(client):
    resp = client.get("/strategy/ideas?risk_level=HIGH")
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_level"] == "HIGH"
    assert isinstance(data["strategies"], list)


def test_create_snapshot_and_allocation_zero(client, test_db):
    db = test_db()
    user = _create_user(db, email="snap@test.com", username="snapuser")
    # Create snapshot
    resp = client.post(f"/users/{user.id}/snapshot")
    assert resp.status_code == 200
    # Allocation with no holdings returns zero total
    resp2 = client.get(f"/users/{user.id}/allocation")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total_value"] == 0


def test_list_transactions_empty(client, test_db):
    db = test_db()
    user = _create_user(db, email="txn@test.com", username="txnuser")
    resp = client.get(f"/users/{user.id}/transactions")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_list_holdings_filter_by_ticker(client, test_db):
    db = test_db()
    user = _create_user(db, email="hold@test.com", username="holduser")
    # Add two holdings
    client.post(f"/users/{user.id}/holdings", json={"ticker": "AAPL", "quantity": 1, "purchase_price": 100})
    client.post(f"/users/{user.id}/holdings", json={"ticker": "MSFT", "quantity": 2, "purchase_price": 200})
    # Filter by ticker
    resp = client.get(f"/users/{user.id}/holdings?ticker=AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["holdings"]) == 1
    assert data["holdings"][0]["ticker"] == "AAPL"


def test_delete_holding_by_id_success(client, test_db):
    db = test_db()
    user = _create_user(db, email="delid@test.com", username="deliduser")
    add = client.post(f"/users/{user.id}/holdings", json={"ticker": "TSLA", "quantity": 1, "purchase_price": 100})
    holding_id = add.json().get("holding_id")
    # Delete by ID should succeed
    resp = client.delete(f"/users/{user.id}/holdings/{holding_id}")
    assert resp.status_code == 200
    assert resp.json().get("status") == "success"


def test_get_user_by_username_fallback(client, test_db):
    db = test_db()
    user = _create_user(db, email="userfallback@test.com", username="fallbackuser")
    # Access by username should resolve user
    resp = client.get(f"/users/{user.username}")
    assert resp.status_code == 200
    assert resp.json().get("username") == user.username


@patch("app.main.get_market_data")
def test_market_quote_endpoint_success(mock_get_market_data, client):
    """Covers /market/quote happy path."""
    mock_get_market_data.side_effect = [
        {"price": 100.0, "change_pct": 1.0, "volume": None, "market_cap": None},
        {"price": 200.0, "change_pct": -0.5, "volume": None, "market_cap": None},
    ]
    resp = client.post("/market/quote", json={"symbols": ["AAPL", "MSFT"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2


@pytest.mark.parametrize("raise_msg", ["Data fetch failed", "upstream error"])
def test_market_quote_endpoint_error(monkeypatch, raise_msg, client):
    """Covers /market/quote exception path by mocking get_client().get_quotes to raise."""
    class BrokenClient:
        def get_quotes(self, symbols):
            raise Exception(raise_msg)

    monkeypatch.setattr("app.main.get_client", lambda: BrokenClient())
    resp = client.post("/market/quote", json={"symbols": ["AAPL"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data


@patch("app.main.run_dividend_screener", return_value={"opportunities": [], "total_dividend_income": 0, "error": None})
def test_market_screen_dividend(mock_div, client):
    resp = client.post("/market/screen", json={"screener_type": "dividend", "params": {"user_id": "user_001"}})
    assert resp.status_code == 200
    data = resp.json()
    assert "opportunities" in data


@patch("app.main.run_growth_screener", return_value={"top_performers": [], "total_unrealized_gains": 0, "error": None})
def test_market_screen_growth(mock_growth, client):
    resp = client.post("/market/screen", json={"screener_type": "growth", "params": {}})
    assert resp.status_code == 200
    data = resp.json()
    assert "top_performers" in data


@patch("app.main.run_value_screener", return_value={"bargain_opportunities": [], "total_unrealized_loss": 0, "error": None})
def test_market_screen_value(mock_value, client):
    resp = client.post("/market/screen", json={"screener_type": "value", "params": {}})
    assert resp.status_code == 200
    data = resp.json()
    assert "bargain_opportunities" in data


def test_market_screen_unknown_type(client):
    resp = client.post("/market/screen", json={"screener_type": "momentum", "params": {}})
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data


@patch("app.main.get_market_data")
def test_market_movers_endpoint(mock_get_market_data, client):
    """Covers /market/movers endpoint."""
    # Return varied change_pct for a few symbols
    def side_effect(sym):
        mapping = {
            "NVDA": {"price": 600.0, "change_pct": 5.0},
            "AAPL": {"price": 180.0, "change_pct": 1.2},
            "MSFT": {"price": 350.0, "change_pct": -0.8},
            "TSLA": {"price": 220.0, "change_pct": 3.4},
            "AMZN": {"price": 150.0, "change_pct": -2.1},
        }
        return mapping.get(sym, {"price": None, "change_pct": None})

    mock_get_market_data.side_effect = side_effect
    resp = client.post("/market/movers", json={"symbols": ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "top_gainers" in data and "top_losers" in data
    assert data.get("count") == 5


@patch("app.main.get_market_data")
def test_market_sectors_endpoint(mock_get_market_data, client):
    """Covers /market/sectors endpoint."""
    # Mock ETF responses
    def side_effect(sym):
        etf_map = {
            "XLK": {"price": 200.0, "change_pct": 0.8},
            "XLV": {"price": 120.0, "change_pct": -0.2},
            "XLF": {"price": 35.0, "change_pct": 0.5},
            "XLE": {"price": 70.0, "change_pct": -1.1},
            "XLI": {"price": 95.0, "change_pct": 0.3},
            "XLY": {"price": 160.0, "change_pct": 1.0},
            "XLB": {"price": 70.0, "change_pct": 0.4},
            "VNQ": {"price": 85.0, "change_pct": -0.6},
            "XLU": {"price": 65.0, "change_pct": 0.1},
            "XLC": {"price": 55.0, "change_pct": 0.2},
        }
        return etf_map.get(sym, {"price": None, "change_pct": None})

    mock_get_market_data.side_effect = side_effect
    resp = client.post("/market/sectors")
    assert resp.status_code == 200
    data = resp.json()
    assert "sectors" in data
    assert isinstance(data["sectors"], list)
