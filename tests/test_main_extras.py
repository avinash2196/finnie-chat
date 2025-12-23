from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db, User


def _setup_db():
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


def test_health_and_metrics_endpoints():
    _setup_db()
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/metrics").status_code == 200


def test_verify_rag_endpoint_no_docs():
    _setup_db()
    client = TestClient(app)
    r = client.post("/verify-rag", params={"query": "What is diversification?"})
    assert r.status_code == 200
    data = r.json()
    assert "rag_documents_found" in data
    assert data["rag_documents_found"] >= 0


def test_add_holding_merge_weighted_cost():
    TestingSessionLocal = _setup_db()
    client = TestClient(app)

    # Create user
    db = TestingSessionLocal()
    user = User(email="merge@test.com", username="mergeuser")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Add first lot: 10 @ 100
    r1 = client.post(f"/users/{user.id}/holdings", json={
        "ticker": "AAPL",
        "quantity": 10,
        "purchase_price": 100.0
    })
    assert r1.status_code == 200

    # Add second lot: 5 @ 200 (should merge to 15 shares, avg cost 133.33)
    r2 = client.post(f"/users/{user.id}/holdings", json={
        "ticker": "AAPL",
        "quantity": 5,
        "purchase_price": 200.0
    })
    assert r2.status_code == 200

    # Verify merged holding
    port = client.get(f"/users/{user.id}/portfolio").json()
    assert port["holdings_count"] == 1
    h = port["holdings"][0]
    assert h["ticker"] == "AAPL"
    assert h["quantity"] == 15
    assert round(h["purchase_price"], 2) == 133.33
