# Finnie-Chat: Implementation Quick Start Guide

## 📋 Current Score Card

```
✅ COMPLETE (70%)
├─ Backend Framework
├─ LLM Integration (3 providers)
├─ Conversation Memory
├─ Market Data Integration
├─ Guardrails & Compliance
├─ 34 Unit Tests
├─ Documentation

⚠️  PARTIAL (30%)
├─ Agents (4/6 complete)
└─ Database Schema (design only)

❌ NOT STARTED (0%)
├─ Frontend UI
├─ Portfolio System
├─ User Authentication
└─ Production Deployment
```

---

## 🚀 Week 1-2: Complete Backend Core

### Task 1: Implement Risk Profiler Agent
**File:** `app/agents/risk_profiler.py`

```python
"""Risk profiler for portfolio analysis."""

from app.mcp.market import get_client
from app.llm import call_llm
import numpy as np

def calculate_portfolio_metrics(holdings_dict):
    """Calculate volatility, Sharpe ratio, beta.
    
    holdings_dict: {
        'AAPL': {'quantity': 10, 'purchase_price': 150},
        'MSFT': {'quantity': 5, 'purchase_price': 300}
    }
    """
    client = get_client()
    
    # Fetch current prices
    prices = {}
    for ticker in holdings_dict.keys():
        quote = client.get_quote(ticker)
        prices[ticker] = quote.price
    
    # Calculate returns (simplified - normally fetch historical)
    returns = []
    for ticker, price in prices.items():
        purchase_price = holdings_dict[ticker]['purchase_price']
        ret = (price - purchase_price) / purchase_price
        returns.append(ret)
    
    # Calculate portfolio metrics
    volatility = np.std(returns) * 100 if returns else 0
    avg_return = np.mean(returns) * 100 if returns else 0
    sharpe_ratio = avg_return / volatility if volatility > 0 else 0
    
    return {
        'volatility': round(volatility, 2),
        'avg_return': round(avg_return, 2),
        'sharpe_ratio': round(sharpe_ratio, 2)
    }

def run(user_message: str, holdings_dict: dict = None):
    """Main risk profiler agent."""
    if not holdings_dict:
        return "No holdings to analyze."
    
    metrics = calculate_portfolio_metrics(holdings_dict)
    
    # Use LLM to explain metrics
    explanation = call_llm(
        system_prompt="You are a risk assessment expert.",
        user_prompt=f"""
        Explain these portfolio metrics in simple terms:
        - Volatility: {metrics['volatility']}%
        - Expected Return: {metrics['avg_return']}%
        - Sharpe Ratio: {metrics['sharpe_ratio']}
        
        What does this tell about the portfolio risk?
        """
    )
    
    return explanation
```

**Testing:** `tests/test_risk_profiler.py`
```python
import pytest
from app.agents.risk_profiler import calculate_portfolio_metrics

def test_portfolio_volatility():
    holdings = {
        'AAPL': {'quantity': 10, 'purchase_price': 150},
        'MSFT': {'quantity': 5, 'purchase_price': 300}
    }
    metrics = calculate_portfolio_metrics(holdings)
    assert 'volatility' in metrics
    assert metrics['volatility'] >= 0

def test_sharpe_ratio():
    holdings = {
        'AAPL': {'quantity': 10, 'purchase_price': 150}
    }
    metrics = calculate_portfolio_metrics(holdings)
    assert 'sharpe_ratio' in metrics
```

**Checklist:**
- [ ] File created: `app/agents/risk_profiler.py` (~80 lines)
- [ ] Unit tests added: `tests/test_risk_profiler.py` (~50 lines)
- [ ] Tests passing: `pytest tests/test_risk_profiler.py -v`
- [ ] Integrated into orchestrator

---

### Task 2: Implement Portfolio Coach Agent
**File:** `app/agents/portfolio_coach.py`

```python
"""Portfolio coach for holdings analysis."""

from app.mcp.market import get_client
from app.llm import call_llm

def analyze_allocation(holdings_dict):
    """Analyze portfolio allocation.
    
    holdings_dict: {
        'AAPL': {'quantity': 10, 'purchase_price': 150},
        'MSFT': {'quantity': 5, 'purchase_price': 300}
    }
    """
    client = get_client()
    
    # Calculate allocation percentages
    total_value = 0
    holdings_with_value = {}
    
    for ticker, holding in holdings_dict.items():
        quote = client.get_quote(ticker)
        value = holding['quantity'] * quote.price
        total_value += value
        holdings_with_value[ticker] = value
    
    allocation = {
        ticker: (value / total_value * 100) if total_value > 0 else 0
        for ticker, value in holdings_with_value.items()
    }
    
    return allocation

def detect_concentration(allocation):
    """Detect if portfolio is too concentrated in one position."""
    max_allocation = max(allocation.values()) if allocation else 0
    if max_allocation > 40:
        return True, max_allocation
    return False, max_allocation

def run(user_message: str, holdings_dict: dict = None):
    """Main portfolio coach agent."""
    if not holdings_dict:
        return "No holdings to analyze."
    
    allocation = analyze_allocation(holdings_dict)
    is_concentrated, max_pct = detect_concentration(allocation)
    
    # Generate recommendations using LLM
    recommendations = call_llm(
        system_prompt="You are an investment portfolio advisor.",
        user_prompt=f"""
        Analyze this portfolio allocation:
        {allocation}
        
        Is it well-diversified? Any recommendations?
        Note: Position > 40% is concentrated.
        Current max position: {max_pct:.1f}%
        """
    )
    
    return recommendations
```

**Testing:** `tests/test_portfolio_coach.py`
```python
import pytest
from app.agents.portfolio_coach import analyze_allocation, detect_concentration

def test_allocation_calculation():
    holdings = {
        'AAPL': {'quantity': 10, 'purchase_price': 150},
        'MSFT': {'quantity': 10, 'purchase_price': 300}
    }
    # Assuming equal weights
    allocation = analyze_allocation(holdings)
    assert 'AAPL' in allocation
    assert 'MSFT' in allocation

def test_concentration_detection():
    allocation = {'AAPL': 60, 'MSFT': 40}
    is_conc, pct = detect_concentration(allocation)
    assert is_conc == True
    assert pct == 60

def test_no_concentration():
    allocation = {'AAPL': 30, 'MSFT': 30, 'GOOGL': 40}
    is_conc, pct = detect_concentration(allocation)
    assert is_conc == False
```

**Checklist:**
- [ ] File created: `app/agents/portfolio_coach.py` (~80 lines)
- [ ] Unit tests added: `tests/test_portfolio_coach.py` (~50 lines)
- [ ] Tests passing
- [ ] Integrated into orchestrator

---

### Task 3: Implement Strategy Agent
**File:** `app/agents/strategy.py`

```python
"""Strategy agent for investment screeners and ideas."""

from app.mcp.market import get_client
from app.rag.store import query_rag
from app.llm import call_llm

def run_dividend_screener(min_yield=0.03):
    """Find dividend stocks."""
    tickers = ['JNJ', 'KO', 'PG', 'MCD', 'V', 'MSFT', 'AAPL']
    client = get_client()
    
    results = []
    for ticker in tickers:
        quote = client.get_quote(ticker)
        # Note: yfinance doesn't always have dividend yield
        # This is a simplified example
        results.append({
            'ticker': ticker,
            'price': quote.price,
            'change': quote.change_pct
        })
    
    return results

def run_growth_screener(min_eps_growth=0.15):
    """Find growth stocks."""
    # Similar structure - fetch stocks with EPS growth > 15%
    tickers = ['NVDA', 'TSLA', 'AVGO', 'ADBE', 'CRM']
    client = get_client()
    
    results = []
    for ticker in tickers:
        quote = client.get_quote(ticker)
        results.append({
            'ticker': ticker,
            'price': quote.price,
            'change': quote.change_pct
        })
    
    return results

def run_value_screener():
    """Find value stocks."""
    tickers = ['GE', 'F', 'BAC', 'C', 'JPM']
    client = get_client()
    
    results = []
    for ticker in tickers:
        quote = client.get_quote(ticker)
        results.append({
            'ticker': ticker,
            'price': quote.price,
            'change': quote.change_pct
        })
    
    return results

def run(user_message: str, screener_type: str = 'dividend'):
    """Main strategy agent."""
    if screener_type == 'dividend':
        results = run_dividend_screener()
        screen_name = "Dividend Stocks"
    elif screener_type == 'growth':
        results = run_growth_screener()
        screen_name = "Growth Stocks"
    else:
        results = run_value_screener()
        screen_name = "Value Stocks"
    
    # Get explanations from RAG
    docs = query_rag(f"How to invest in {screen_name.lower()}")
    context = "\n".join(docs) if docs else ""
    
    # Generate strategy using LLM
    strategy = call_llm(
        system_prompt="You are an investment strategist.",
        user_prompt=f"""
        Here are {screen_name}: {results[:3]}
        
        Based on these stocks and this context:
        {context}
        
        What are the pros and cons of this strategy?
        """
    )
    
    return {
        'screener': screen_name,
        'results': results[:5],
        'strategy': strategy
    }
```

**Testing:** `tests/test_strategy.py`
```python
import pytest
from app.agents.strategy import run_dividend_screener, run_growth_screener

def test_dividend_screener():
    results = run_dividend_screener()
    assert len(results) > 0
    assert 'ticker' in results[0]
    assert 'price' in results[0]

def test_growth_screener():
    results = run_growth_screener()
    assert len(results) > 0
    assert 'ticker' in results[0]

def test_strategy_execution():
    strategy = run("Show me dividend stocks", screener_type='dividend')
    assert 'screener' in strategy
    assert 'results' in strategy
    assert 'strategy' in strategy
```

**Checklist:**
- [ ] File created: `app/agents/strategy.py` (~100 lines)
- [ ] Unit tests added: `tests/test_strategy.py` (~50 lines)
- [ ] Tests passing
- [ ] Integrated into orchestrator

---

### Task 4: Design Database Schema
**File:** `app/models.py`

```python
"""SQLAlchemy models for Finnie database."""

from sqlalchemy import Column, String, Decimal, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    """User account."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    risk_profile = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    holdings = relationship("Holding", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

class Holding(Base):
    """User portfolio holding."""
    __tablename__ = "holdings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False)
    quantity = Column(Decimal(10, 4), nullable=False)
    purchase_price = Column(Decimal(10, 2), nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="holdings")

class Transaction(Base):
    """Transaction log."""
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False)
    action = Column(String, nullable=False)  # BUY, SELL, DIVIDEND
    quantity = Column(Decimal(10, 4), nullable=False)
    price = Column(Decimal(10, 2), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="transactions")

class UserProfile(Base):
    """Extended user profile."""
    __tablename__ = "user_profiles"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    risk_tolerance = Column(String)  # Conservative, Moderate, Aggressive
    investment_horizon = Column(String)  # Short-term, Medium-term, Long-term
    annual_income = Column(String)
    investment_goals = Column(String)  # Retirement, Growth, Income, etc.
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Checklist:**
- [ ] File created: `app/models.py` (~100 lines)
- [ ] Add to `requirements.txt`: sqlalchemy, psycopg2-binary
- [ ] Database URI configured in .env
- [ ] Migration script created

---

### Task 5: Add Database Integration Tests

**File:** `tests/test_models.py`

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, Holding, Transaction
from datetime import datetime

@pytest.fixture
def db():
    """SQLite test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_create_user(db):
    user = User(email="test@example.com", name="Test User")
    db.add(user)
    db.commit()
    
    assert user.id is not None
    assert user.email == "test@example.com"

def test_add_holding(db):
    user = User(email="test@example.com")
    db.add(user)
    db.commit()
    
    holding = Holding(
        user_id=user.id,
        ticker="AAPL",
        quantity=10,
        purchase_price=150,
        purchase_date=datetime.now()
    )
    db.add(holding)
    db.commit()
    
    assert holding.user_id == user.id
    assert holding.ticker == "AAPL"

def test_add_transaction(db):
    user = User(email="test@example.com")
    db.add(user)
    db.commit()
    
    txn = Transaction(
        user_id=user.id,
        ticker="AAPL",
        action="BUY",
        quantity=10,
        price=150,
        transaction_date=datetime.now()
    )
    db.add(txn)
    db.commit()
    
    assert txn.action == "BUY"
```

**Checklist:**
- [ ] File created: `tests/test_models.py` (~80 lines)
- [ ] All tests passing
- [ ] Database schema validated

---

## Week 1-2 Summary

**Deliverables:**
- ✅ 3 new agents implemented (Risk, Portfolio Coach, Strategy)
- ✅ Database models designed
- ✅ 15 new unit tests added
- ✅ Total tests: 50+
- ✅ Backend 90% complete

**Git commit:**
```bash
git add app/agents/ app/models.py tests/
git commit -m "Complete backend agents and database models

- Implemented Risk Profiler Agent (volatility, Sharpe ratio)
- Implemented Portfolio Coach Agent (allocation analysis)
- Implemented Strategy Agent (screeners)
- Added SQLAlchemy models (User, Holding, Transaction)
- Added 15 unit tests for new agents and models
- Total test coverage: 50+ tests"
```

---

## Week 3-5: Build Chat Tab UI

**Skip to ROADMAP.md Phase 2 section for detailed UI implementation.**

### Quick Start: Streamlit Setup

```bash
# Create frontend directory
mkdir -p frontend
cd frontend

# Install Streamlit
pip install streamlit requests plotly pandas

# Create app structure
mkdir pages
touch app.py
touch pages/01_📝_Chat.py
touch pages/02_📊_Portfolio.py
touch pages/03_📈_Market_Trends.py
```

**Minimal Chat Tab** (`frontend/pages/01_📝_Chat.py`):
```python
import streamlit as st
import requests

st.title("💬 Chat with Finnie")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conv_id" not in st.session_state:
    st.session_state.conv_id = None

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
if prompt := st.chat_input("Ask me anything about finance..."):
    # Send to backend
    try:
        resp = requests.post("http://localhost:8000/chat", json={
            "message": prompt,
            "conversation_id": st.session_state.conv_id
        })
        data = resp.json()
        
        # Store conversation ID
        st.session_state.conv_id = data["conversation_id"]
        
        # Add to messages
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": data["reply"]})
        
        # Rerun to display
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
```

**Run it:**
```bash
streamlit run app.py
# Open http://localhost:8501
```

---

## Week 6-8: Portfolio System

See ROADMAP.md Phase 3 for database setup and portfolio endpoints.

---

## Week 9-10: Market Trends

See ROADMAP.md Phase 4 for screeners and market tab.

---

## Week 11-12: Deploy

See ROADMAP.md Phase 5 for Docker and production setup.

---

## Key Commands Cheat Sheet

### Backend
```bash
# Start server
python -m uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_risk_profiler.py -v

# Check coverage
pytest tests/ --cov=app
```

### Database (PostgreSQL)
```bash
# Local PostgreSQL with Docker
docker run -d -e POSTGRES_PASSWORD=secret -p 5432:5432 postgres:15

# Create database
psql -h localhost -U postgres -c "CREATE DATABASE finnie_db;"

# Run migrations (when using Alembic)
alembic upgrade head
```

### Frontend
```bash
# Streamlit
streamlit run frontend/app.py

# Access at http://localhost:8501
```

### Git
```bash
# Commit with message
git add .
git commit -m "Feature description"

# Push to repository
git push origin main
```

---

## Testing Coverage Goals

```
Week 1-2:  50 tests  (agents + models)
Week 3-5:  60 tests  (add UI tests)
Week 6-8:  80 tests  (add DB tests)
Week 9-10: 100 tests (add integration tests)
Week 11-12: 120+ tests (target 80%+ coverage)
```

---

## Questions?

- **Technical Issues?** → Check ARCHITECTURE.md
- **Feature Details?** → Check REQUIREMENTS_ANALYSIS.md
- **Timeline?** → Check ROADMAP.md
- **API Reference?** → See app/main.py or /docs endpoint

**Next Step:** Start Week 1-2 tasks above. Implement the 3 agents first.

Good luck! 🚀
