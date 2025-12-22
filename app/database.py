"""
Database Models for Finnie Chat
Uses SQLAlchemy ORM with PostgreSQL (or SQLite for development)
"""
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
import os

# Database URL - use PostgreSQL in production, SQLite in development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finnie_chat.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== MODELS ====================

class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    risk_tolerance = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH
    portfolio_value = Column(Float, default=0.0)  # Cached total
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # External API credentials (encrypted in production)
    robinhood_token = Column(String, nullable=True)
    fidelity_token = Column(String, nullable=True)
    schwab_token = Column(String, nullable=True)
    
    # Relationships
    holdings = relationship("Holding", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="user", cascade="all, delete-orphan")


class Holding(Base):
    """Stock holding in user's portfolio"""
    __tablename__ = "holdings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), index=True)
    ticker = Column(String, index=True)
    quantity = Column(Float)
    purchase_price = Column(Float)
    purchase_date = Column(DateTime)
    current_price = Column(Float, default=0.0)  # Synced from market data
    total_value = Column(Float, default=0.0)  # quantity * current_price
    gain_loss = Column(Float, default=0.0)  # (current - purchase) * quantity
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="holdings")


class Transaction(Base):
    """Buy/Sell/Dividend transactions"""
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), index=True)
    ticker = Column(String, index=True)
    transaction_type = Column(String)  # BUY, SELL, DIVIDEND
    quantity = Column(Float)
    price = Column(Float)  # Price per share
    total_amount = Column(Float)  # quantity * price
    transaction_date = Column(DateTime, index=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="transactions")


class PortfolioSnapshot(Base):
    """Historical snapshot of portfolio (for analytics)"""
    __tablename__ = "portfolio_snapshots"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), index=True)
    total_value = Column(Float)
    cash_balance = Column(Float, default=0.0)
    snapshot_date = Column(DateTime, index=True, default=datetime.utcnow)
    
    # Performance metrics (cached)
    daily_return = Column(Float, default=0.0)
    monthly_return = Column(Float, default=0.0)
    yearly_return = Column(Float, default=0.0)
    
    # Risk metrics (cached)
    volatility = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="snapshots")


class SyncLog(Base):
    """Track external API syncs"""
    __tablename__ = "sync_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), index=True)
    source = Column(String)  # ROBINHOOD, FIDELITY, SCHWAB, MOCK
    status = Column(String)  # SUCCESS, FAILED, PENDING
    message = Column(String, nullable=True)
    synced_items = Column(Integer, default=0)  # How many holdings synced
    sync_time_ms = Column(Integer)  # How long it took
    synced_at = Column(DateTime, default=datetime.utcnow)


# ==================== UTILITY FUNCTIONS ====================

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
