"""
Database model tests
Tests CRUD operations, relationships, and data integrity
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import (
    Base, User, Holding, Transaction, PortfolioSnapshot,
    SyncLog, SessionLocal
)

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create test database"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


class TestUserModel:
    """Test User model"""
    
    def test_create_user(self, test_db):
        """Test creating a user"""
        user = User(
            email="test@example.com",
            username="testuser",
            risk_tolerance="MEDIUM"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.portfolio_value == 0.0
    
    def test_user_constraints(self, test_db):
        """Test unique constraints"""
        user1 = User(email="test@example.com", username="user1")
        test_db.add(user1)
        test_db.commit()
        
        user2 = User(email="test@example.com", username="user2")
        test_db.add(user2)
        
        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()
    
    def test_user_timestamps(self, test_db):
        """Test timestamp fields"""
        user = User(email="test@example.com", username="user")
        test_db.add(user)
        test_db.commit()
        
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_at <= user.updated_at


class TestHoldingModel:
    """Test Holding model"""
    
    def test_create_holding(self, test_db):
        """Test creating a holding"""
        user = User(email="test@example.com", username="user")
        test_db.add(user)
        test_db.commit()
        
        holding = Holding(
            user_id=user.id,
            ticker="AAPL",
            quantity=10.0,
            purchase_price=150.0,
            current_price=160.0,
            total_value=1600.0,
            gain_loss=100.0,
            purchase_date=datetime.utcnow()
        )
        test_db.add(holding)
        test_db.commit()
        test_db.refresh(holding)
        
        assert holding.id is not None
        assert holding.ticker == "AAPL"
        assert holding.quantity == 10.0
        assert holding.total_value == 1600.0
    
    def test_holding_relationship(self, test_db):
        """Test user-holding relationship"""
        user = User(email="test@example.com", username="user")
        test_db.add(user)
        test_db.commit()
        
        holding1 = Holding(
            user_id=user.id, ticker="AAPL", quantity=10,
            purchase_price=150, purchase_date=datetime.utcnow()
        )
        holding2 = Holding(
            user_id=user.id, ticker="MSFT", quantity=5,
            purchase_price=350, purchase_date=datetime.utcnow()
        )
        test_db.add_all([holding1, holding2])
        test_db.commit()
        
        # Verify relationship
        assert len(user.holdings) == 2
        assert all(h.user_id == user.id for h in user.holdings)
    
    def test_holding_cascading_delete(self, test_db):
        """Test that deleting user deletes holdings"""
        user = User(email="test@example.com", username="user")
        test_db.add(user)
        test_db.commit()
        
        holding = Holding(
            user_id=user.id, ticker="AAPL", quantity=10,
            purchase_price=150, purchase_date=datetime.utcnow()
        )
        test_db.add(holding)
        test_db.commit()
        
        holding_id = holding.id
        
        # Delete user
        test_db.delete(user)
        test_db.commit()
        
        # Verify holding is deleted
        deleted_holding = test_db.query(Holding).filter(Holding.id == holding_id).first()
        assert deleted_holding is None


class TestTransactionModel:
    """Test Transaction model"""
    
    def test_create_transaction(self, test_db):
        """Test creating a transaction"""
        user = User(email="test@example.com", username="user")
        test_db.add(user)
        test_db.commit()
        
        txn = Transaction(
            user_id=user.id,
            ticker="AAPL",
            transaction_type="BUY",
            quantity=10.0,
            price=150.0,
            total_amount=1500.0,
            transaction_date=datetime.utcnow()
        )
        test_db.add(txn)
        test_db.commit()
        test_db.refresh(txn)
        
        assert txn.id is not None
        assert txn.transaction_type == "BUY"
        assert txn.total_amount == 1500.0
    
    def test_transaction_types(self, test_db):
        """Test different transaction types"""
        user = User(email="test@example.com", username="user")
        test_db.add(user)
        test_db.commit()
        
        txn_buy = Transaction(
            user_id=user.id, ticker="AAPL", transaction_type="BUY",
            quantity=10, price=150, total_amount=1500,
            transaction_date=datetime.utcnow()
        )
        txn_sell = Transaction(
            user_id=user.id, ticker="AAPL", transaction_type="SELL",
            quantity=5, price=160, total_amount=800,
            transaction_date=datetime.utcnow()
        )
        txn_div = Transaction(
            user_id=user.id, ticker="AAPL", transaction_type="DIVIDEND",
            quantity=10, price=0.25, total_amount=2.50,
            transaction_date=datetime.utcnow()
        )
        
        test_db.add_all([txn_buy, txn_sell, txn_div])
        test_db.commit()
        
        txns = test_db.query(Transaction).filter(Transaction.user_id == user.id).all()
        assert len(txns) == 3
        assert {t.transaction_type for t in txns} == {"BUY", "SELL", "DIVIDEND"}


class TestPortfolioSnapshotModel:
    """Test PortfolioSnapshot model"""
    
    def test_create_snapshot(self, test_db):
        """Test creating a snapshot"""
        user = User(email="test@example.com", username="user")
        test_db.add(user)
        test_db.commit()
        
        snapshot = PortfolioSnapshot(
            user_id=user.id,
            total_value=10000.0,
            daily_return=2.5,
            volatility=0.15
        )
        test_db.add(snapshot)
        test_db.commit()
        test_db.refresh(snapshot)
        
        assert snapshot.id is not None
        assert snapshot.total_value == 10000.0
        assert snapshot.daily_return == 2.5
    
    def test_snapshot_history(self, test_db):
        """Test creating multiple snapshots for history"""
        user = User(email="test@example.com", username="user")
        test_db.add(user)
        test_db.commit()
        
        # Create snapshots over time
        for i in range(5):
            snapshot = PortfolioSnapshot(
                user_id=user.id,
                total_value=10000.0 + (i * 100),
                snapshot_date=datetime.utcnow() - timedelta(days=5-i)
            )
            test_db.add(snapshot)
        test_db.commit()
        
        # Query snapshots
        snapshots = test_db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.user_id == user.id
        ).order_by(PortfolioSnapshot.snapshot_date).all()
        
        assert len(snapshots) == 5
        assert snapshots[-1].total_value > snapshots[0].total_value


class TestSyncLogModel:
    """Test SyncLog model"""
    
    def test_create_sync_log(self, test_db):
        """Test creating sync log"""
        user = User(email="test@example.com", username="user")
        test_db.add(user)
        test_db.commit()
        
        log = SyncLog(
            user_id=user.id,
            source="ROBINHOOD",
            status="SUCCESS",
            synced_items=5,
            sync_time_ms=1200
        )
        test_db.add(log)
        test_db.commit()
        test_db.refresh(log)
        
        assert log.id is not None
        assert log.source == "ROBINHOOD"
        assert log.status == "SUCCESS"
        assert log.synced_items == 5


class TestDataIntegrity:
    """Test data integrity and constraints"""
    
    def test_portfolio_value_calculation(self, test_db):
        """Test portfolio value is correctly calculated"""
        user = User(email="test@example.com", username="user")
        test_db.add(user)
        test_db.commit()
        
        # Add holdings
        h1 = Holding(
            user_id=user.id, ticker="AAPL", quantity=10,
            purchase_price=150, current_price=160,
            total_value=1600, gain_loss=100,
            purchase_date=datetime.utcnow()
        )
        h2 = Holding(
            user_id=user.id, ticker="MSFT", quantity=5,
            purchase_price=350, current_price=360,
            total_value=1800, gain_loss=50,
            purchase_date=datetime.utcnow()
        )
        test_db.add_all([h1, h2])
        test_db.commit()
        
        # Calculate total
        holdings = test_db.query(Holding).filter(Holding.user_id == user.id).all()
        total_value = sum(h.total_value for h in holdings)
        total_gain_loss = sum(h.gain_loss for h in holdings)
        
        assert total_value == 3400.0
        assert total_gain_loss == 150.0
    
    def test_transaction_history_integrity(self, test_db):
        """Test transaction history matches holdings"""
        user = User(email="test@example.com", username="user")
        test_db.add(user)
        test_db.commit()
        
        # Buy transaction
        buy_txn = Transaction(
            user_id=user.id, ticker="AAPL", transaction_type="BUY",
            quantity=10, price=150, total_amount=1500,
            transaction_date=datetime.utcnow()
        )
        test_db.add(buy_txn)
        test_db.commit()
        
        # Verify transaction created
        txns = test_db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.ticker == "AAPL"
        ).all()
        
        assert len(txns) == 1
        assert txns[0].total_amount == 1500.0
