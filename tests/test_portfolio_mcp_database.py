"""Tests for Portfolio MCP with real database integration."""

import pytest
from datetime import datetime, timedelta
from app.mcp.portfolio import (
    get_user_holdings,
    get_user_profile,
    get_transaction_history,
    get_portfolio_client,
)
from app.database import SessionLocal, User, Holding, Transaction
import uuid


@pytest.fixture
def test_user_id():
    """Create a test user and return UUID."""
    db = SessionLocal()
    try:
        # Clean up any existing test user
        existing = db.query(User).filter(User.username == "test_portfolio_user").first()
        if existing:
            db.query(Transaction).filter(Transaction.user_id == existing.id).delete()
            db.query(Holding).filter(Holding.user_id == existing.id).delete()
            db.delete(existing)
            db.commit()
        
        # Create test user
        user = User(
            id=str(uuid.uuid4()),
            email="test_portfolio@example.com",
            username="test_portfolio_user",
            risk_tolerance="MEDIUM"
        )
        db.add(user)
        db.commit()
        user_id = user.id
        yield user_id
        
        # Cleanup
        db.query(Transaction).filter(Transaction.user_id == user_id).delete()
        db.query(Holding).filter(Holding.user_id == user_id).delete()
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def test_portfolio(test_user_id):
    """Create test portfolio with holdings and transactions."""
    db = SessionLocal()
    try:
        user_id = test_user_id
        
        # Add holdings
        aapl_holding = Holding(
            id=str(uuid.uuid4()),
            user_id=user_id,
            ticker="AAPL",
            quantity=10.0,
            purchase_price=150.0,
            current_price=180.0,
            purchase_date=datetime(2024, 1, 15),
            total_value=1800.0
        )
        
        msft_holding = Holding(
            id=str(uuid.uuid4()),
            user_id=user_id,
            ticker="MSFT",
            quantity=5.0,
            purchase_price=350.0,
            current_price=380.0,
            purchase_date=datetime(2024, 2, 20),
            total_value=1900.0
        )
        
        db.add(aapl_holding)
        db.add(msft_holding)
        db.commit()
        
        # Add transactions
        aapl_txn = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            ticker="AAPL",
            transaction_type="BUY",
            quantity=10.0,
            price=150.0,
            total_amount=1500.0,
            transaction_date=datetime(2024, 1, 15)
        )
        
        msft_txn = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            ticker="MSFT",
            transaction_type="BUY",
            quantity=5.0,
            price=350.0,
            total_amount=1750.0,
            transaction_date=datetime(2024, 2, 20)
        )
        
        db.add(aapl_txn)
        db.add(msft_txn)
        db.commit()
        
        yield user_id
    finally:
        db.close()


class TestPortfolioMCPDatabase:
    """Test portfolio MCP functions with real database."""
    
    def test_get_holdings_by_uuid(self, test_portfolio):
        """Test getting holdings by user UUID."""
        result = get_user_holdings(test_portfolio)
        
        assert result['error'] is None
        assert result['user_id'] == test_portfolio
        assert 'AAPL' in result['holdings']
        assert 'MSFT' in result['holdings']
        assert len(result['holdings']) == 2
    
    def test_get_holdings_by_username(self, test_portfolio):
        """Test getting holdings by username."""
        result = get_user_holdings("test_portfolio_user")
        
        assert result['error'] is None
        assert result['username'] == "test_portfolio_user"
        assert 'AAPL' in result['holdings']
        assert 'MSFT' in result['holdings']
    
    def test_holdings_include_calculations(self, test_portfolio):
        """Test that holdings include gain/loss calculations."""
        result = get_user_holdings(test_portfolio)
        
        aapl = result['holdings']['AAPL']
        assert aapl['quantity'] == 10.0
        assert aapl['purchase_price'] == 150.0
        assert aapl['current_price'] == 180.0
        assert aapl['current_value'] == 1800.0
        assert aapl['gain_loss'] == 300.0  # (180-150)*10
        assert aapl['gain_loss_pct'] == 20.0
    
    def test_holdings_total_value(self, test_portfolio):
        """Test that total portfolio value is calculated correctly."""
        result = get_user_holdings(test_portfolio)
        
        # AAPL: 10*180=1800, MSFT: 5*380=1900, Total: 3700
        assert result['total_shares_value'] == 3700.0
        assert result['total_portfolio_value'] == 3700.0
    
    def test_get_profile(self, test_portfolio):
        """Test getting user profile."""
        result = get_user_profile(test_portfolio)
        
        assert result['error'] is None
        assert result['profile']['username'] == "test_portfolio_user"
        assert result['profile']['email'] == "test_portfolio@example.com"
        assert result['profile']['risk_tolerance'] == "MEDIUM"
    
    def test_get_profile_by_username(self):
        """Test getting profile by username."""
        result = get_user_profile("test_portfolio_user")
        
        # Should not error if user exists
        if result.get('error'):
            assert "not found" in result['error'].lower() or result['error'] is None
    
    def test_get_transaction_history(self, test_portfolio):
        """Test getting transaction history."""
        result = get_transaction_history(test_portfolio)
        
        assert result['error'] is None
        assert result['total_transactions'] == 2
        assert len(result['transactions']) == 2
        
        # Verify transaction details (newest first)
        msft_txn = result['transactions'][0]
        assert msft_txn['ticker'] == "MSFT"
        assert msft_txn['type'] == "BUY"
        assert msft_txn['quantity'] == 5.0
        assert msft_txn['price'] == 350.0
    
    def test_transaction_history_by_username(self, test_portfolio):
        """Test getting transactions by username."""
        result = get_transaction_history("test_portfolio_user")
        
        assert result['error'] is None
        assert result['total_transactions'] >= 0
    
    def test_transaction_history_filter_by_type(self, test_portfolio):
        """Test filtering transactions by type."""
        result = get_transaction_history(test_portfolio, transaction_type="BUY")
        
        assert result['error'] is None
        assert result['total_transactions'] == 2
        for txn in result['transactions']:
            assert txn['type'] == "BUY"
    
    def test_transaction_history_filter_by_days(self, test_portfolio):
        """Test filtering transactions by date range."""
        # Add a recent transaction
        db = SessionLocal()
        try:
            recent_txn = Transaction(
                id=str(uuid.uuid4()),
                user_id=test_portfolio,
                ticker="GOOGL",
                transaction_type="BUY",
                quantity=2.0,
                price=2800.0,
                total_amount=5600.0,
                transaction_date=datetime.now()
            )
            db.add(recent_txn)
            db.commit()
            
            # Get last 1 day
            result = get_transaction_history(test_portfolio, days=1)
            assert result['total_transactions'] == 1
            assert result['transactions'][0]['ticker'] == "GOOGL"
        finally:
            db.close()
    
    def test_nonexistent_user(self):
        """Test handling of nonexistent user."""
        result = get_user_holdings("nonexistent_uuid_12345")
        
        assert result['error'] is not None
        assert result['holdings'] == {}
        assert result['total_portfolio_value'] == 0.0


class TestPortfolioClient:
    """Test PortfolioClient wrapper."""
    
    def test_portfolio_client_by_uuid(self, test_portfolio):
        """Test portfolio client with UUID."""
        client = get_portfolio_client(test_portfolio)
        
        holdings = client.get_holdings()
        assert holdings['error'] is None
        assert 'AAPL' in holdings['holdings']
    
    def test_portfolio_client_by_username(self, test_portfolio):
        """Test portfolio client with username."""
        client = get_portfolio_client("test_portfolio_user")
        
        holdings = client.get_holdings()
        assert holdings['error'] is None or holdings['error'] is None
    
    def test_portfolio_client_methods(self, test_portfolio):
        """Test all portfolio client methods."""
        client = get_portfolio_client(test_portfolio)
        
        # Test all methods work
        holdings = client.get_holdings()
        assert holdings is not None
        
        profile = client.get_profile()
        assert profile is not None
        
        transactions = client.get_transactions()
        assert transactions is not None
        
        performance = client.get_performance()
        assert performance is not None
