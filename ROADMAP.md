# Finnie-Chat: Visual Development Roadmap

## Current Status (Today)

```
┌────────────────────────────────────────────────────────┐
│                 FINNIE-CHAT MVP STATUS                │
│                                                        │
│  Backend:        ████████░░░░░░░░░░░░ 70%            │
│  Agents:         ██████░░░░░░░░░░░░░░░░ 50%          │
│  Frontend:       ░░░░░░░░░░░░░░░░░░░░░░  0%          │
│  Portfolio:      ░░░░░░░░░░░░░░░░░░░░░░  0%          │
│  Testing:        ██████████░░░░░░░░░░░░ 65%          │
│  Documentation:  ███████░░░░░░░░░░░░░░░░ 60%          │
│                                                        │
│  Overall: ████████░░░░░░░░░░░░░░░░░░░░ 41%           │
└────────────────────────────────────────────────────────┘
```

---

## Timeline Overview

```
Week 1-2: COMPLETE BACKEND CORE
├─ ✅ Finish all 6 agents
├─ ✅ Build portfolio DB schema
├─ ✅ Add 15+ unit tests
└─ Deploy locally working

Week 3-5: BUILD FRONTEND MVP
├─ Choose: Streamlit or React
├─ Chat Tab UI (fully working)
├─ Portfolio Tab (placeholder)
├─ Market Tab (placeholder)
└─ Connect to backend (/chat endpoint)

Week 6-8: IMPLEMENT PORTFOLIO SYSTEM
├─ PostgreSQL database setup
├─ Holdings CRUD endpoints
├─ Portfolio Coach Agent (full)
├─ Portfolio Tab UI (complete)
└─ Risk analysis working

Week 9-10: IMPLEMENT MARKET TRENDS
├─ Strategy Agent (full)
├─ Screener engine (5+ types)
├─ Market data aggregation
├─ Market Tab UI (complete)
└─ Investment ideas working

Week 11-12: POLISH & DEPLOY
├─ User authentication (optional)
├─ Performance optimization
├─ Docker containerization
├─ Testing to 80%+ coverage
└─ Production deployment
```

---

## Detailed Phase Breakdown

### PHASE 1: Backend Core Completion (Weeks 1-2)

#### Current State
```
Agents Implemented:
✅ Educator Agent (RAG)
✅ Market Agent (yFinance)
✅ Compliance Agent (rules)
❌ Portfolio Coach (stub → IMPLEMENT)
❌ Risk Profiler (stub → IMPLEMENT)
❌ Strategy (stub → IMPLEMENT)
```

#### What to Build

**1. Risk Profiler Agent** (Portfolio Risk Analysis)
```python
# Calculate:
- Portfolio volatility (standard deviation)
- Sharpe ratio (risk-adjusted returns)
- Beta (market sensitivity)
- Correlation matrix
- Value at Risk (VaR)

# Data sources:
- User holdings (from DB)
- Historical prices (from yFinance)
- Risk-free rate (from market data)

# Example output:
"Your portfolio has 18% volatility, 
Sharpe ratio of 1.2, and beta of 0.95"
```

**2. Portfolio Coach Agent** (Holdings Analysis)
```python
# Analyze:
- Asset allocation vs. targets
- Concentration risk
- Sector concentration
- Diversification score
- Rebalancing recommendations

# Data sources:
- User holdings (from DB)
- Current market prices
- User risk profile

# Example output:
"Your portfolio is 60% tech (concentrated). 
Consider adding 15% bonds for balance."
```

**3. Strategy Agent** (Screeners & Ideas)
```python
# Run screeners:
- Dividend yield screeners
- Growth stock screeners  
- Value stock screeners
- Sector leaders
- Momentum plays

# Generate ideas:
- Mean reversion trades
- Sector rotation ideas
- Dividend income strategies

# Data sources:
- Market APIs
- MCP server (analytics)
- RAG (strategy docs)
```

#### Database Schema to Design
```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE,
  risk_profile VARCHAR (LOW/MED/HIGH),
  investment_goals TEXT,
  created_at TIMESTAMP
);

-- Portfolio Holdings
CREATE TABLE holdings (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users,
  ticker VARCHAR,
  quantity DECIMAL,
  purchase_price DECIMAL,
  purchase_date DATE,
  added_at TIMESTAMP
);

-- Transactions
CREATE TABLE transactions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users,
  ticker VARCHAR,
  action VARCHAR (BUY/SELL/DIVIDEND),
  quantity DECIMAL,
  price DECIMAL,
  date DATE,
  transaction_date TIMESTAMP
);

-- User Profiles
CREATE TABLE user_profiles (
  user_id UUID PRIMARY KEY REFERENCES users,
  risk_tolerance VARCHAR,
  investment_horizon VARCHAR,
  income_level VARCHAR,
  updated_at TIMESTAMP
);
```

#### Testing Additions
```
Add 15+ tests:
test_risk_profiler_volatility()
test_risk_profiler_sharpe_ratio()
test_portfolio_coach_analysis()
test_portfolio_coach_rebalancing()
test_strategy_dividend_screener()
test_strategy_growth_screener()
test_strategy_value_screener()
... etc
```

**Checklist:**
- [ ] Risk Profiler Agent implemented (40 lines of code)
- [ ] Portfolio Coach Agent implemented (50 lines of code)
- [ ] Strategy Agent implemented (60 lines of code)
- [ ] Database schema designed
- [ ] 15 new unit tests added
- [ ] All tests passing (50+ total)

**Duration:** 7-10 days

---

### PHASE 2: Frontend MVP (Weeks 3-5)

#### Technology Decision Matrix

```
STREAMLIT (Recommended for MVP)
├─ Pros:
│  ├─ Built-in charts (plotly, matplotlib)
│  ├─ Python-native (no Node.js needed)
│  ├─ Fast development (3-4 weeks)
│  ├─ Hot reload
│  └─ Great for dashboards
├─ Cons:
│  ├─ Limited customization
│  ├─ Not ideal for mobile
│  └─ Slower for real-time updates
└─ Best for: MVP, internal tools

REACT (Recommended for v2.0)
├─ Pros:
│  ├─ Full control over UI
│  ├─ Better performance
│  ├─ Mobile-friendly
│  ├─ Rich ecosystem (D3, Recharts)
│  └─ Production-grade
├─ Cons:
│  ├─ Requires Node.js + npm
│  ├─ Longer development (6-8 weeks)
│  ├─ Learning curve
│  └─ More dependencies
└─ Best for: Production, scalable UX
```

**Recommendation:** **Use Streamlit for MVP, migrate to React in v2.0**

#### Streamlit App Structure

```
frontend/
├─ app.py                      # Main entry point
├─ pages/
│  ├─ 01_📝_Chat.py            # Chat Tab
│  ├─ 02_📊_Portfolio.py        # Portfolio Tab
│  └─ 03_📈_Market_Trends.py    # Market Trends Tab
├─ components/
│  ├─ chat_ui.py               # Chat input/display
│  ├─ portfolio_ui.py          # Portfolio charts
│  └─ market_ui.py             # Market display
├─ utils/
│  ├─ api_client.py            # FastAPI client
│  └─ formatting.py            # Response formatting
└─ requirements.txt            # Dependencies
```

#### Frontend Implementation

**Chat Tab UI** (app/pages/01_📝_Chat.py)
```python
import streamlit as st
import requests

st.set_page_config(page_title="Finnie Chat", layout="wide")
st.title("💬 Chat with Finnie")

# Initialize session state
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input field
if user_input := st.chat_input("Ask about finance..."):
    # Send to backend
    response = requests.post("http://localhost:8000/chat", json={
        "message": user_input,
        "conversation_id": st.session_state.conversation_id
    })
    
    data = response.json()
    st.session_state.conversation_id = data["conversation_id"]
    
    # Display response
    with st.chat_message("assistant"):
        st.write(data["reply"])
    
    # Store in session
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": data["reply"]})
```

**Portfolio Tab UI** (app/pages/02_📊_Portfolio.py) - Placeholder
```python
import streamlit as st

st.title("📊 Portfolio Insights")
st.info("Portfolio tracking coming in Phase 3...")

# Placeholder cards
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Value", "$0", "+0%")
with col2:
    st.metric("Allocation", "0 holdings")
with col3:
    st.metric("Risk Score", "N/A")
```

**Market Tab UI** (app/pages/03_📈_Market_Trends.py) - Placeholder
```python
import streamlit as st

st.title("📈 Market Trends")
st.info("Market analysis coming in Phase 4...")

# Placeholder tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Heatmap", "Screeners"])
with tab1:
    st.write("Market overview coming soon...")
with tab2:
    st.write("Sector heatmap coming soon...")
with tab3:
    st.write("Stock screeners coming soon...")
```

**Checklist:**
- [ ] Streamlit project created
- [ ] Chat Tab fully working
- [ ] Portfolio Tab placeholder
- [ ] Market Tab placeholder
- [ ] Connected to FastAPI backend
- [ ] Session state management working
- [ ] 5+ UI tests added

**Duration:** 10-12 days

---

### PHASE 3: Portfolio System (Weeks 6-8)

#### What to Build

**1. PostgreSQL Database Setup**
```bash
# Install PostgreSQL
brew install postgresql@15  # Mac
# or use Docker:
docker run -d \
  -e POSTGRES_PASSWORD=secret \
  -p 5432:5432 \
  postgres:15

# Create database
createdb finnie_db
```

**2. SQLAlchemy Models**
```python
# app/models.py
from sqlalchemy import Column, String, Decimal, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    email = Column(String, unique=True)
    risk_profile = Column(String, default="MEDIUM")
    created_at = Column(DateTime, default=datetime.utcnow)

class Holding(Base):
    __tablename__ = "holdings"
    id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    ticker = Column(String)
    quantity = Column(Decimal)
    purchase_price = Column(Decimal)
    purchase_date = Column(DateTime)
    added_at = Column(DateTime, default=datetime.utcnow)
```

**3. API Endpoints for Portfolio**
```python
# app/main.py - Add these endpoints

@app.post("/portfolio/holdings")
def add_holding(user_id: str, ticker: str, quantity: float, purchase_price: float):
    # Add holding to database
    # Return: {"status": "ok", "holding_id": "..."}

@app.get("/portfolio/holdings/{user_id}")
def get_holdings(user_id: str):
    # Fetch all holdings for user
    # Return: [{"ticker": "AAPL", "quantity": 10, ...}]

@app.get("/portfolio/analysis/{user_id}")
def analyze_portfolio(user_id: str):
    # Call Portfolio Coach Agent
    # Return: {"allocation": {...}, "recommendations": [...]}

@app.delete("/portfolio/holdings/{holding_id}")
def remove_holding(holding_id: str):
    # Delete holding
```

**4. Portfolio Coach Agent Enhancement**
```python
# app/agents/portfolio_coach.py
from app.models import Holding, User
from app.mcp.market import get_client
from app.llm import call_llm

def analyze_portfolio(user_id: str):
    # Fetch user holdings
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    
    # Fetch current prices
    client = get_client()
    quotes = {h.ticker: client.get_quote(h.ticker) for h in holdings}
    
    # Calculate allocation
    total_value = sum(h.quantity * quotes[h.ticker].price for h in holdings)
    allocation = {
        h.ticker: (h.quantity * quotes[h.ticker].price / total_value) * 100
        for h in holdings
    }
    
    # Use LLM to generate insights
    analysis = call_llm(
        system="You are a portfolio analysis expert.",
        user_prompt=f"Analyze this allocation: {allocation}"
    )
    
    return {
        "allocation": allocation,
        "total_value": total_value,
        "analysis": analysis
    }
```

**5. Portfolio Tab UI Enhancement**
```python
# frontend/pages/02_📊_Portfolio.py
import streamlit as st
import requests
import plotly.express as px

st.title("📊 Portfolio Insights")

# Get user ID (from session or form)
user_id = st.session_state.get("user_id") or st.text_input("Enter your ID")

if user_id:
    # Fetch portfolio
    response = requests.get(f"http://localhost:8000/portfolio/holdings/{user_id}")
    holdings = response.json()
    
    # Display holdings table
    st.dataframe(holdings)
    
    # Fetch analysis
    response = requests.get(f"http://localhost:8000/portfolio/analysis/{user_id}")
    analysis = response.json()
    
    # Display allocation pie chart
    fig = px.pie(
        values=analysis["allocation"].values(),
        names=analysis["allocation"].keys(),
        title="Asset Allocation"
    )
    st.plotly_chart(fig)
    
    # Display analysis
    st.info(f"**Analysis:** {analysis['analysis']}")
    
    # Add holding form
    st.subheader("Add Holding")
    ticker = st.text_input("Ticker")
    quantity = st.number_input("Quantity")
    price = st.number_input("Purchase Price")
    if st.button("Add"):
        requests.post(f"http://localhost:8000/portfolio/holdings", json={
            "user_id": user_id,
            "ticker": ticker,
            "quantity": quantity,
            "purchase_price": price
        })
        st.success("Added!")
```

**Checklist:**
- [ ] PostgreSQL running locally
- [ ] SQLAlchemy models created
- [ ] Database migrations done
- [ ] CRUD endpoints working
- [ ] Portfolio Coach Agent enhanced
- [ ] Portfolio Tab UI complete
- [ ] 10+ database tests added

**Duration:** 14-21 days

---

### PHASE 4: Market Trends System (Weeks 9-10)

#### What to Build

**1. Market Data Aggregation**
```python
# app/agents/market_analyst.py
import yfinance as yf

def get_market_overview():
    """Fetch S&P 500, NASDAQ, Dow indices"""
    indices = {
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ',
        '^DJI': 'Dow Jones'
    }
    
    overview = {}
    for ticker, name in indices.items():
        t = yf.Ticker(ticker)
        price = t.info.get('regularMarketPrice')
        change = t.info.get('regularMarketChangePercent')
        overview[name] = {'price': price, 'change': change}
    
    return overview

def get_sector_performance():
    """Fetch sector performance"""
    sectors = ['XLK', 'XLV', 'XLI', 'XLY', 'XLE', 'XLRE', 'XLU', 'XLF', 'XLB']
    
    sector_data = {}
    for etf in sectors:
        t = yf.Ticker(etf)
        change = t.info.get('regularMarketChangePercent')
        sector_data[etf] = change
    
    return sector_data

def get_top_movers():
    """Fetch top gainers and losers"""
    # Use market API or MCP server
    # Return: {"gainers": [...], "losers": [...]}
```

**2. Strategy Agent Enhancement**
```python
# app/agents/strategy.py

def run_dividend_screener():
    """Find high-dividend stocks"""
    # Criteria: yield > 3%, payout ratio < 70%
    results = []
    for ticker in ['MSFT', 'AAPL', 'JNJ', 'KO', 'PG']:  # Sample
        t = yf.Ticker(ticker)
        yield_ = t.info.get('dividendYield', 0)
        if yield_ and yield_ > 0.03:
            results.append({
                'ticker': ticker,
                'yield': yield_,
                'price': t.info.get('regularMarketPrice')
            })
    return results

def run_growth_screener():
    """Find growth stocks"""
    # Criteria: EPS growth > 15%
    # Implementation similar to dividend screener

def run_value_screener():
    """Find value stocks"""
    # Criteria: P/E < market average
    # Implementation similar
```

**3. Market Tab UI Enhancement**
```python
# frontend/pages/03_📈_Market_Trends.py
import streamlit as st
import requests
import plotly.express as px

st.title("📈 Market Trends")

# Tab 1: Market Overview
tab1, tab2, tab3 = st.tabs(["Overview", "Heatmap", "Screeners"])

with tab1:
    st.subheader("Market Indices")
    
    # Fetch overview
    response = requests.get("http://localhost:8000/market/overview")
    overview = response.json()
    
    # Display cards
    col1, col2, col3 = st.columns(3)
    for i, (name, data) in enumerate(overview.items()):
        with [col1, col2, col3][i]:
            st.metric(name, f"${data['price']:.0f}", f"{data['change']:.2f}%")

with tab2:
    st.subheader("Sector Performance Heatmap")
    
    # Fetch sector data
    response = requests.get("http://localhost:8000/market/sectors")
    sectors = response.json()
    
    # Display heatmap
    df = pd.DataFrame(list(sectors.items()), columns=['Sector', 'Change %'])
    fig = px.bar(df, x='Sector', y='Change %', color='Change %')
    st.plotly_chart(fig)

with tab3:
    st.subheader("Stock Screeners")
    
    screener_type = st.radio("Select Screener", ["Dividends", "Growth", "Value"])
    
    if screener_type == "Dividends":
        response = requests.get("http://localhost:8000/screeners/dividend")
    elif screener_type == "Growth":
        response = requests.get("http://localhost:8000/screeners/growth")
    else:
        response = requests.get("http://localhost:8000/screeners/value")
    
    results = response.json()
    st.dataframe(results)
```

**Checklist:**
- [ ] Market data aggregation working
- [ ] Strategy Agent screeners implemented (5+ types)
- [ ] Market Analyst Agent enhanced
- [ ] Market Tab UI complete with heatmap
- [ ] Screener results displaying
- [ ] 8+ market integration tests added

**Duration:** 10-14 days

---

### PHASE 5: Polish & Deploy (Weeks 11-12)

#### Deployment Checklist

**1. Docker Setup**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**2. Production Configuration**
```bash
# .env.production
OPENAI_API_KEY=...
DATABASE_URL=postgresql://user:pass@host:5432/finnie_db
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**3. Testing to 80%+**
- [ ] Add 20+ integration tests
- [ ] Add 10+ UI tests
- [ ] Run coverage report
- [ ] Target: 80%+ code coverage

**4. Documentation**
- [ ] API documentation (Swagger at /docs)
- [ ] Deployment guide
- [ ] Configuration guide
- [ ] Troubleshooting guide

**Checklist:**
- [ ] Docker image builds
- [ ] Database migrations run
- [ ] Tests pass (80%+ coverage)
- [ ] Deployed to staging
- [ ] Performance testing done
- [ ] Documentation complete

**Duration:** 7-10 days

---

## Feature Completeness Matrix

### By Week

```
Week 1-2:
┌─────────────────────────────┐
│ Agents             ████░░░░░│ 67%
│ Database Schema    ████░░░░░│ 40%
│ Testing            ███░░░░░░│ 30%
└─────────────────────────────┘

Week 3-5:
┌─────────────────────────────┐
│ Frontend (Chat)    ████████░│ 90%
│ Frontend (Port)    ██░░░░░░░│ 20%
│ Frontend (Market)  ██░░░░░░░│ 20%
└─────────────────────────────┘

Week 6-8:
┌─────────────────────────────┐
│ Portfolio DB       ████████░│ 85%
│ Portfolio Agent    ████████░│ 85%
│ Portfolio UI       ████████░│ 85%
└─────────────────────────────┘

Week 9-10:
┌─────────────────────────────┐
│ Market API         ███████░░│ 75%
│ Strategy Agent     ███████░░│ 75%
│ Market UI          ███████░░│ 75%
└─────────────────────────────┘

Week 11-12:
┌─────────────────────────────┐
│ Testing            ████████░│ 80%+
│ Deployment         ████████░│ 90%
│ Documentation      ████████░│ 85%
└─────────────────────────────┘
```

---

## Success Criteria by Phase

### Phase 1: ✅ MVP Backend
- [ ] 6 agents fully operational
- [ ] 50+ tests passing
- [ ] Database schema finalized
- [ ] All endpoints documented

### Phase 2: ✅ MVP Frontend
- [ ] Chat tab fully functional
- [ ] Connected to backend
- [ ] Conversation history working
- [ ] 10+ UI tests

### Phase 3: ✅ Portfolio System
- [ ] PostgreSQL live
- [ ] Holdings tracked
- [ ] Portfolio analysis working
- [ ] Portfolio tab complete

### Phase 4: ✅ Market Trends
- [ ] 5+ screeners working
- [ ] Market data flowing
- [ ] Market tab complete
- [ ] 80+ tests total

### Phase 5: ✅ Production Ready
- [ ] 80%+ test coverage
- [ ] Deployed to server
- [ ] Monitoring active
- [ ] Complete documentation

---

## Key Metrics

```
Lines of Code:
- Backend Core:       ~2,000 lines (DONE)
- Frontend:           ~1,500 lines (TODO)
- Database:           ~800 lines (TODO)
- Tests:              ~2,000 lines (PARTIAL)
Total MVP:            ~6,300 lines

Test Coverage:
- Current:            65% (34 tests)
- Target MVP:         75% (50 tests)
- Target v1.0:        80%+ (100 tests)

Performance Targets:
- Chat response time:  < 2 seconds
- Portfolio load:      < 1 second
- API latency:         < 500ms
- Cache hit rate:      > 30%
```

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Delays in Phase 2** | Frontend blocked | Start with Streamlit (fast) |
| **Database issues** | Portfolio system down | Use SQLite in dev, PostgreSQL in prod |
| **LLM API failures** | No responses | Multi-provider gateway (✅ done) |
| **Poor test coverage** | Bugs in production | 80%+ target, catch early |
| **Scope creep** | Timeline slips | Strict MVP scope, v2.0 for nice-to-haves |

---

## Next Steps Summary

1. **Week 1:** Complete 6 agents + database schema
2. **Week 2-3:** Build chat tab UI (Streamlit)
3. **Week 4-6:** Portfolio system + UI
4. **Week 7-8:** Market trends + screeners
5. **Week 9-10:** Testing + optimization
6. **Week 11-12:** Deploy to production

**Start Date:** This week
**Target MVP Launch:** 5-6 weeks
**Target v1.0 Launch:** 10-12 weeks

---

**Questions? See REQUIREMENTS_ANALYSIS.md for detailed gap information.**
