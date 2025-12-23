from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db, Holding, User


def _setup_memory_db():
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
    return TestingSessionLocal


def test_market_quote_endpoint_with_mocked_client():
    TestingSessionLocal = _setup_memory_db()
    client = TestClient(app)

    # Insert a minimal user to keep parity with other flows
    db = TestingSessionLocal()
    user = User(email="u@e.com", username="u")
    db.add(user)
    db.commit()

    with patch("app.agents.market._client") as mock_client:
        mock_quote = MagicMock(price=100.0, change_pct=1.5, currency="USD")
        mock_client.get_quote.return_value = mock_quote
        resp = client.post("/market/quote", json={"symbols": ["AAPL", "MSFT"]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert data["quotes"]["AAPL"]["price"] == 100.0


def test_strategy_ideas_endpoint_levels():
    _setup_memory_db()
    client = TestClient(app)
    for level in ["LOW", "MEDIUM", "HIGH"]:
        r = client.get(f"/strategy/ideas?risk_level={level}")
        assert r.status_code == 200
        payload = r.json()
        assert payload["risk_level"] == level
        assert len(payload["strategies"]) >= 1


def test_analytics_and_performance_minimal_data():
    TestingSessionLocal = _setup_memory_db()
    client = TestClient(app)

    # Create a user and one holding to ensure analytics path runs
    db = TestingSessionLocal()
    user = User(email="a@b.com", username="ab")
    db.add(user)
    db.commit()
    db.refresh(user)

    h = Holding(
        user_id=user.id,
        ticker="AAPL",
        quantity=1,
        purchase_price=100.0,
        current_price=110.0,
        total_value=110.0,
        gain_loss=10.0,
    )
    db.add(h)
    db.commit()

    # Analytics should return computed fields
    ra = client.get(f"/users/{user.id}/analytics")
    assert ra.status_code == 200
    d = ra.json()
    assert d.get("total_value") == 110.0
    assert "sharpe_ratio" in d
    assert "volatility" in d

    # Performance: no snapshots yet, empty list is fine
    rp = client.get(f"/users/{user.id}/performance?days=7")
    assert rp.status_code == 200
    assert rp.json()["count"] == 0


def test_screeners_endpoint_all_types():
    TestingSessionLocal = _setup_memory_db()
    client = TestClient(app)

    # Create a user for context
    db = TestingSessionLocal()
    user = User(email="s@t.com", username="st")
    db.add(user)
    db.commit()
    db.refresh(user)

    for screener in ["dividend", "growth", "value"]:
        r = client.post(
            "/market/screen",
            json={"screener_type": screener, "params": {"user_id": user.id}},
        )
        assert r.status_code == 200
        payload = r.json()
        assert "error" in payload  # function returns error None when fine

    # Unknown screener should return error payload
    r = client.post(
        "/market/screen",
        json={"screener_type": "unknown", "params": {"user_id": user.id}},
    )
    assert r.status_code == 200
    assert "error" in r.json()
