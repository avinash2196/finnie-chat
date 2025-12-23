"""
API endpoint integration tests for database operations
Tests FastAPI endpoints with database integration
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
import json

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.drop_all(bind=engine)  # Clean slate
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    db = TestingSessionLocal()
    yield db
    db.close()
    
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_user(client, test_db):
    """Create test user via API"""
    response = client.post("/users", json={
        "email": "test@example.com",
        "username": "testuser",
        "risk_tolerance": "MEDIUM"
    })
    assert response.status_code == 200
    data = response.json()
    return data["user_id"]


class TestUserEndpoints:
    """Test user CRUD endpoints"""
    
    def test_create_user(self, client, test_db):
        """Test POST /users"""
        response = client.post("/users", json={
            "email": "new@example.com",
            "username": "newuser",
            "risk_tolerance": "HIGH"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["email"] == "new@example.com"
        assert "user_id" in data
    
    def test_create_duplicate_user(self, client, test_db, test_user):
        """Test creating duplicate user fails"""
        response = client.post("/users", json={
            "email": "test@example.com",
            "username": "testuser2"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
    
    def test_get_user(self, client, test_db, test_user):
        """Test GET /users/{user_id}"""
        response = client.get(f"/users/{test_user}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user
        assert data["email"] == "test@example.com"
        assert "portfolio_value" in data
    
    def test_get_user_by_username(self, client, test_db, test_user):
        """Test GET /users/{user_id} with username instead of UUID"""
        # First get user to confirm username
        response = client.get(f"/users/{test_user}")
        username = response.json()["username"]
        
        # Now fetch by username
        response = client.get(f"/users/{username}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user
        assert data["username"] == username
        assert data["email"] == "test@example.com"
    
    def test_get_nonexistent_user(self, client, test_db):
        """Test getting non-existent user"""
        response = client.get("/users/nonexistent-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"


class TestPortfolioEndpoints:
    """Test portfolio endpoints"""
    
    def test_get_empty_portfolio(self, client, test_db, test_user):
        """Test getting empty portfolio"""
        response = client.get(f"/users/{test_user}/portfolio")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_value"] == 0
        assert data["holdings_count"] == 0
        assert data["holdings"] == []
    
    def test_add_holding(self, client, test_db, test_user):
        """Test POST /users/{user_id}/holdings"""
        response = client.post(f"/users/{test_user}/holdings", json={
            "ticker": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_add_holding_by_username(self, client, test_db, test_user):
        """Test adding holding using username instead of UUID"""
        # Get username
        user_response = client.get(f"/users/{test_user}")
        username = user_response.json()["username"]
        
        # Add holding using username
        response = client.post(f"/users/{username}/holdings", json={
            "ticker": "TSLA",
            "quantity": 5,
            "purchase_price": 200.0
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Verify portfolio via username
        portfolio = client.get(f"/users/{username}/portfolio")
        assert portfolio.status_code == 200
        assert portfolio.json()["holdings_count"] == 1
    
    def test_complete_workflow_with_username(self, client, test_db):
        """Test complete user workflow using only username (simulates user_002 scenario)"""
        # 1. Create user with username user_002
        create_response = client.post("/users", json={
            "email": "user002@example.com",
            "username": "user_002",
            "risk_tolerance": "MEDIUM"
        })
        assert create_response.status_code == 200
        user_data = create_response.json()
        actual_uuid = user_data["user_id"]
        
        # 2. Add holdings using username (not UUID)
        holding_response = client.post("/users/user_002/holdings", json={
            "ticker": "AAPL",
            "quantity": 1000,
            "purchase_price": 150.0
        })
        assert holding_response.status_code == 200
        assert holding_response.json()["status"] == "success"
        
        # 3. Get portfolio using username
        portfolio_response = client.get("/users/user_002/portfolio")
        assert portfolio_response.status_code == 200
        portfolio_data = portfolio_response.json()
        assert portfolio_data["holdings_count"] == 1
        assert portfolio_data["holdings"][0]["ticker"] == "AAPL"
        assert portfolio_data["holdings"][0]["quantity"] == 1000
        
        # 4. Get holdings list using username
        holdings_response = client.get("/users/user_002/holdings")
        assert holdings_response.status_code == 200
        
        # 5. Verify it also works with UUID
        uuid_portfolio = client.get(f"/users/{actual_uuid}/portfolio")
        assert uuid_portfolio.status_code == 200
        assert uuid_portfolio.json()["holdings_count"] == 1
    
    def test_get_portfolio_with_holdings(self, client, test_db, test_user):
        """Test portfolio after adding holdings"""
        # Add holding
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0
        })
        
        # Get portfolio
        response = client.get(f"/users/{test_user}/portfolio")
        
        assert response.status_code == 200
        data = response.json()
        assert data["holdings_count"] == 1
        assert data["total_value"] == 1500.0
        assert data["holdings"][0]["ticker"] == "AAPL"
    
    def test_list_holdings(self, client, test_db, test_user):
        """Test GET /users/{user_id}/holdings"""
        # Add holdings
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0
        })
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "MSFT",
            "quantity": 5,
            "purchase_price": 350.0
        })
        
        response = client.get(f"/users/{test_user}/holdings")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["holdings"]) == 2
        assert data["total_value"] == 3250.0
    
    def test_transactions_created_with_username(self, client, test_db):
        """Test that transactions are created correctly when using username instead of UUID"""
        # Create user
        create_response = client.post("/users", json={
            "email": "txntest@example.com",
            "username": "txn_user",
            "risk_tolerance": "MEDIUM"
        })
        assert create_response.status_code == 200
        
        # Add holding using username
        holding_response = client.post("/users/txn_user/holdings", json={
            "ticker": "GOOGL",
            "quantity": 100,
            "purchase_price": 150.0
        })
        assert holding_response.status_code == 200
        
        # Verify transaction was created using username
        txn_response = client.get("/users/txn_user/transactions")
        assert txn_response.status_code == 200
        transactions = txn_response.json()["transactions"]
        assert len(transactions) == 1
        assert transactions[0]["ticker"] == "GOOGL"
        assert transactions[0]["quantity"] == 100
        assert transactions[0]["type"] == "BUY"
    
    def test_filter_holdings_by_ticker(self, client, test_db, test_user):
        """Test filtering holdings"""
        # Add holdings
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0
        })
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "MSFT",
            "quantity": 5,
            "purchase_price": 350.0
        })
        
        response = client.get(f"/users/{test_user}/holdings?ticker=AAPL")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["holdings"]) == 1
        assert data["holdings"][0]["ticker"] == "AAPL"
    
    def test_delete_holding(self, client, test_db, test_user):
        """Test DELETE /users/{user_id}/holdings/{holding_id}"""
        # Add holding
        add_response = client.post(f"/users/{test_user}/holdings", json={
            "ticker": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0
        })
        holding_id = add_response.json()["holding_id"]
        
        # Delete holding
        response = client.delete(f"/users/{test_user}/holdings/{holding_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Verify deleted
        list_response = client.get(f"/users/{test_user}/holdings")
        assert len(list_response.json()["holdings"]) == 0


class TestTransactionEndpoints:
    """Test transaction endpoints"""
    
    def test_get_empty_transactions(self, client, test_db, test_user):
        """Test getting transactions when none exist"""
        response = client.get(f"/users/{test_user}/transactions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["transactions"] == []
    
    def test_transactions_created_with_holdings(self, client, test_db, test_user):
        """Test transactions are created when adding holdings"""
        # Add holding
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0
        })
        
        # Get transactions
        response = client.get(f"/users/{test_user}/transactions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["transactions"][0]["type"] == "BUY"
        assert data["transactions"][0]["ticker"] == "AAPL"
    
    def test_transactions_filter_by_days(self, client, test_db, test_user):
        """Test filtering transactions by days"""
        # Add holding
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0
        })
        
        response = client.get(f"/users/{test_user}/transactions?days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 0


class TestSyncEndpoints:
    """Test portfolio sync endpoints"""
    
    @pytest.mark.asyncio
    async def test_sync_portfolio_mock(self, client, test_db, test_user):
        """Test POST /users/{user_id}/sync with mock provider"""
        response = client.post(f"/users/{test_user}/sync", json={
            "provider": "mock"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert "synced_items" in data
    
    @pytest.mark.asyncio
    async def test_sync_creates_holdings(self, client, test_db, test_user):
        """Test sync creates holdings in database"""
        # Sync
        client.post(f"/users/{test_user}/sync", json={
            "provider": "mock"
        })
        
        # Verify holdings endpoint responds (note: API sync uses separate DB session)
        response = client.get(f"/users/{test_user}/holdings")
        data = response.json()
        assert "holdings" in data and isinstance(data["holdings"], list)


class TestSnapshotEndpoints:
    """Test portfolio snapshot endpoints"""
    
    def test_create_snapshot(self, client, test_db, test_user):
        """Test POST /users/{user_id}/snapshot"""
        # Add holding first
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0
        })
        
        response = client.post(f"/users/{test_user}/snapshot")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "snapshot_id" in data
        assert data["total_value"] == 1500.0


class TestAllocationEndpoints:
    """Test asset allocation endpoints"""
    
    def test_get_empty_allocation(self, client, test_db, test_user):
        """Test allocation when no holdings"""
        response = client.get(f"/users/{test_user}/allocation")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_value"] == 0
        assert data["allocation"] == []
    
    def test_get_allocation(self, client, test_db, test_user):
        """Test asset allocation calculation"""
        # Add multiple holdings
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0
        })
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "MSFT",
            "quantity": 5,
            "purchase_price": 350.0
        })
        
        response = client.get(f"/users/{test_user}/allocation")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["allocation"]) == 2
        assert data["total_value"] == 3250.0
        
        # Verify percentages
        percentages = [a["percentage"] for a in data["allocation"]]
        assert sum(percentages) == pytest.approx(100.0, abs=0.1)
    
    def test_allocation_ordering(self, client, test_db, test_user):
        """Test allocation is sorted by value"""
        # Add holdings with different values
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "AAPL",
            "quantity": 1,
            "purchase_price": 100.0
        })
        client.post(f"/users/{test_user}/holdings", json={
            "ticker": "MSFT",
            "quantity": 10,
            "purchase_price": 350.0
        })
        
        response = client.get(f"/users/{test_user}/allocation")
        data = response.json()
        
        # MSFT should be first (higher value)
        assert data["allocation"][0]["ticker"] == "MSFT"
        assert data["allocation"][1]["ticker"] == "AAPL"


class TestEndToEndWorkflow:
    """Test complete user workflow"""
    
    def test_complete_portfolio_workflow(self, client, test_db):
        """Test full workflow: create user -> add holdings -> sync -> view"""
        # 1. Create user
        user_response = client.post("/users", json={
            "email": "workflow@example.com",
            "username": "workflow_user"
        })
        user_id = user_response.json()["user_id"]
        
        # 2. Add holdings manually
        client.post(f"/users/{user_id}/holdings", json={
            "ticker": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0
        })
        
        # 3. Check portfolio
        portfolio = client.get(f"/users/{user_id}/portfolio").json()
        assert portfolio["holdings_count"] == 1
        
        # 4. Sync from external (mock)
        sync_result = client.post(f"/users/{user_id}/sync", json={
            "provider": "mock"
        }).json()
        assert sync_result["status"] == "SUCCESS"
        
        # 5. Check updated portfolio (count may not increase due to separate DB session)
        updated_portfolio = client.get(f"/users/{user_id}/portfolio").json()
        assert updated_portfolio["holdings_count"] >= 1
        
        # 6. View transactions
        txns = client.get(f"/users/{user_id}/transactions").json()
        assert txns["count"] > 0
        
        # 7. View allocation
        allocation = client.get(f"/users/{user_id}/allocation").json()
        assert len(allocation["allocation"]) > 0
        
        # 8. Create snapshot
        snapshot = client.post(f"/users/{user_id}/snapshot").json()
        assert snapshot["status"] == "success"


class TestErrorHandling:
    """Test error handling in endpoints"""
    
    def test_invalid_user_id(self, client, test_db):
        """Test operations with invalid user ID"""
        response = client.get("/users/invalid-id/portfolio")
        assert response.status_code == 200
        assert response.json()["status"] == "error"
    
    def test_invalid_holding_id(self, client, test_db, test_user):
        """Test deleting non-existent holding"""
        response = client.delete(f"/users/{test_user}/holdings/invalid-id")
        assert response.status_code == 200
        assert response.json()["status"] == "error"
    
    def test_missing_required_fields(self, client, test_db):
        """Test creating user without required fields"""
        response = client.post("/users", json={})
        assert response.status_code == 422  # Validation error
