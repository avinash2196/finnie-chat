# finnie-chat

Local FastAPI-based financial AI assistant with Orchestrator + 6 specialized agents, database-backed portfolio management, conversation memory, MCP servers for market data and portfolio, RAG-based education, multi-provider AI Gateway, comprehensive portfolio analytics, and **enterprise observability** with Arize AI and LangSmith.

## Recent Updates (December 2025)

✅ **Observability & Monitoring** — Switched to Arize AI and LangSmith for tracing, quality/safety signals, tagging, performance metrics, and error tracking.

✅ **Portfolio MCP Database Integration** — Replaced hardcoded mock data with real SQLite database queries. Portfolio MCP functions now fetch actual user holdings, transactions, and profiles directly from the database.

✅ **Chat Portfolio Access** — Fixed `/chat` endpoint to pass `user_id` to orchestrator, enabling agents to access user portfolio data during conversations.

✅ **Compliance Agent Deduplication** — Fixed duplicate disclaimer messages by checking if disclaimer already exists before appending.

✅ **Test Coverage Expansion** — Added 26+ new tests: 11 for Portfolio MCP database integration, 10 for compliance agent, 5 for DeepEval portfolio chat scenarios.

## Overview

finnie-chat is a sophisticated financial AI system that combines:
- **6 Specialized Agents** for education, market analysis, risk profiling, portfolio coaching, strategy selection, and compliance
- **Agentic Orchestration** with intelligent routing and context awareness
- **Enterprise Observability** with Arize AI + LangSmith for monitoring, tracing, and debugging
- **Database Integration** with SQLAlchemy (SQLite/PostgreSQL) for portfolio persistence
- **Multi-Provider Portfolio Sync** (Mock, Robinhood, Fidelity) with background scheduler
- **Portfolio Analytics** with Sharpe ratio, volatility, and diversification metrics
- **Performance Tracking** with historical snapshots and trend analysis
- **Market Trends & Analysis** with stock screeners and strategy ideas
- **Conversation Memory** with persistent storage (JSON)
- **Multi-provider LLM Gateway** (OpenAI primary, Gemini/Anthropic fallback) with caching
- **Dual MCP Servers**: Market data (yFinance) + Portfolio management (database-backed)
- **RAG Engine** (TF-IDF) for trusted financial knowledge retrieval with verification
- **Guardrails** for input validation and compliance filtering
- **REST API** with 20+ endpoints for portfolio and market operations
- **Streamlit Frontend** with multi-tab UI (Chat, Portfolio, Market Trends)

## Architecture

```
User Request
    │
    ├─ Conversation Memory (context retrieval)
    │
    ├─ Intent Classification (determine domain)
    │
    └─ Orchestrator (agent routing) ◄─ LangSmith Tracing
        │
        ├─ [Educator Agent] ◄─ RAG Engine + Verification
        ├─ [Market Agent] ◄─ Market MCP Server (yFinance)
        ├─ [Risk Profiler Agent] ◄─ Portfolio MCP Server
        ├─ [Portfolio Coach Agent] ◄─ Portfolio MCP Server
        ├─ [Strategy Agent] ◄─ Market MCP Server
            └─ [Compliance Agent] ◄─ Safety guardrails
            │
            └─ AI Gateway (3 providers) ◄─ Arize + LangSmith
                ├─ OpenAI GPT-4o-mini (primary)
                ├─ Google Gemini (fallback)
                └─ Anthropic Claude (fallback)
            │
            └─ Response + Memory (store in conversation history)
            └─ Anthropic (fallback)
            │
            └─ Response + Memory (store in conversation history)

Database Layer (SQLAlchemy)
    │
    ├─ User Management
    ├─ Portfolio Holdings
    ├─ Transaction History
        └─ Provider Pattern (Multi-source sync)
            ├─ Mock Provider (development)
            ├─ Robinhood Provider (external API)
            └─ Fidelity Provider (external API)

    ### Updated Architecture Diagram

    An updated diagram reflecting recent changes (MCP batching, aggregation cache, optional Redis, observability hooks, and Streamlit frontend) is available at:

    - [Architecture Diagram](docs/architecture/architecture_diagram.svg)

    ### Developer Notes

    - **Aggregation cache**: The in-memory short-TTL aggregation cache `_quote_agg_cache` is used to reduce repeated quote fetches. Enable Redis fallback by setting `REDIS_URL` in `.env` to use a shared cache in production.
    - **MCP batching & parallelism**: Market MCP now batches ticker requests and runs per-ticker fetches in parallel workers to reduce latency and external calls.
    - **Observability**: LangSmith and Arize integrations are safe no-ops when API keys are not present; tracing and timing middleware were added to `app/main.py`. Use `OBSERVABILITY` env vars to configure providers.
    - **Profiling artifacts**: A `coverage.xml` and profiling artifacts (py-spy flamegraphs) are generated during CI runs and saved in the project root when enabled.
    - **Manual/Full test runs**: To run the full matrix (including manual tests) set `RUN_MANUAL_TESTS=1` in your environment before running pytest.

    If you'd like additional diagram formats (PNG, PDF) or a sequence/data-flow diagram, tell me which and I'll add them.
```

## Database Integration ✅

**Fully Implemented** - The project now includes comprehensive database integration:

### Features
- **SQLAlchemy ORM** with SQLite (dev) and PostgreSQL (production) support
- **5 Database Models**: User, Holding, Transaction, PortfolioSnapshot, SyncLog
- **Provider Pattern**: Easily switch between Mock, Robinhood, Fidelity data sources
- **Background Sync**: Automatic hourly portfolio synchronization

### Quick Database Start
```powershell
# Initialize database
python -c "from app.database import init_db; init_db()"

# Run demo
python scripts/db_utils/demo_database.py

# Sync portfolio from mock provider
curl -X POST http://localhost:8000/users/{user_id}/sync -d '{"provider":"mock"}'
```

See [docs/architecture/DATABASE_GUIDE.md](docs/architecture/DATABASE_GUIDE.md) for complete documentation.

---

## Observability & Monitoring ✅

**Enterprise-Ready** - Production monitoring with Arize AI and LangSmith:

### Features
- **LangSmith** — Hierarchical run traces: intent → router → agents → final composer
- **Arize AI** — Prediction logging with tags, quality (groundedness, relevance, risk) and safety signals
- **Custom Tracking** — Agent execution times, chat interactions, performance metrics

### Quick Setup
```powershell
# Add to .env (optional - works without)
echo "LANGSMITH_API_KEY=lsv2_pt_..." >> .env
echo "LANGSMITH_PROJECT=finnie-chat" >> .env
echo "ARIZE_API_KEY=your-arize-api-key" >> .env
echo "ARIZE_SPACE_KEY=your-arize-space-key" >> .env
echo "ARIZE_ORG_KEY=optional-org-key" >> .env
echo "PROMPT_VERSION=v1" >> .env
echo "AGENT_VERSION=1.0.0" >> .env
```

### Check Status
```bash
# View observability status
curl http://localhost:8000/observability/status

# Or visit: http://localhost:8000/docs
```

**What's Tracked Automatically:**
- ✅ Chat response times by intent and risk level
- ✅ Agent execution performance (individual and total)
- ✅ LLM run hierarchy (intent → router → agents → composer) in LangSmith
- ✅ Arize tags: `prediction_type`, `model_version`, `prompt_version`, `agent_type`, `asset_type`, `compliance_category`
- ✅ Arize quality: `groundedness_score`, `retrieval_relevance`, `hallucination_risk`, `confidence_level`
- ✅ Arize safety: `pii_detected`, `restricted_advice_triggered`, `refusal_reason`

See [docs/architecture/OBSERVABILITY.md](docs/architecture/OBSERVABILITY.md) for complete guide.

---

## Quick Start

### Get the code
View the repository on GitHub: https://github.com/avinash2196/finnie-chat

```powershell
git clone https://github.com/avinash2196/finnie-chat.git
cd finnie-chat
```

Repository docs: https://github.com/avinash2196/finnie-chat/tree/main/docs

### Setup
```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create .env with your LLM API keys
echo "OPENAI_API_KEY=sk-proj-..." > .env
echo "GEMINI_API_KEY=your-gemini-key" >> .env
echo "GEMINI_ENDPOINT=https://generativelanguage.googleapis.com/v1/models/gemini-proto:generate" >> .env
```

### Run Server

# Server runs on http://127.0.0.1:8000
# Interactive API docs: http://127.0.0.1:8000/docs
# ReDoc: http://127.0.0.1:8000/redoc
```

### Run Tests

```powershell
# Run all tests (200+ tests)
.\venv\Scripts\python.exe -m pytest tests -v

# Quick run (quiet mode)
.\venv\Scripts\python.exe -m pytest tests -q

# Test specific modules
.\venv\Scripts\python.exe -m pytest tests/test_portfolio_mcp_database.py -v       # Portfolio MCP Database Integration (11 tests)
.\venv\Scripts\python.exe -m pytest tests/test_compliance_agent.py -v              # Compliance Agent Dedup (10 tests)
.\venv\Scripts\python.exe -m pytest tests/deepeval/test_deepeval_portfolio_chat.py -v  # DeepEval Portfolio Chat (5 tests)

# Run specific agent tests (2 tests each)
.\venv\Scripts\python.exe -m pytest tests/test_risk_profiler.py::TestRiskProfilerAgent::test_no_holdings tests/test_risk_profiler.py::TestRiskProfilerAgent::test_run_with_holdings -v

.\venv\Scripts\python.exe -m pytest tests/test_portfolio_coach.py::TestPortfolioCoachAgent::test_agent_with_holdings tests/test_portfolio_coach.py::TestPortfolioCoachAgent::test_agent_no_holdings -v

.\venv\Scripts\python.exe -m pytest tests/test_strategy.py::TestStrategyAgent::test_agent_dividend_strategy tests/test_strategy.py::TestStrategyAgent::test_agent_growth_strategy -v


**Full Suite:**
```
======================================= test session starts ========================================
collected 183 items

tests/compliance_test.py::test_no_disclaimer_for_low_risk PASSED                              [  0%]
tests/test_gateway.py::test_gateway_loads_openai_from_env PASSED                              [  8%]
tests/test_risk_profiler.py::TestRiskProfilerAgent::test_run_with_holdings PASSED             [ 86%]
tests/test_portfolio_coach.py::TestPortfolioCoachAgent::test_agent_with_holdings PASSED       [ 55%]
```

**Agent-Specific Tests:**
```powershell
# RiskProfilerAgent (2 tests, 14.72s)
$ .\venv\Scripts\python.exe -m pytest tests/test_risk_profiler.py::TestRiskProfilerAgent::test_no_holdings tests/test_risk_profiler.py::TestRiskProfilerAgent::test_run_with_holdings -v
tests/test_risk_profiler.py::TestRiskProfilerAgent::test_no_holdings PASSED                   [ 50%]
tests/test_risk_profiler.py::TestRiskProfilerAgent::test_run_with_holdings PASSED             [100%]
======================================== 2 passed in 14.72s ========================================

# PortfolioCoachAgent (2 tests, 16.71s)
$ .\venv\Scripts\python.exe -m pytest tests/test_portfolio_coach.py::TestPortfolioCoachAgent::test_agent_with_holdings tests/test_portfolio_coach.py::TestPortfolioCoachAgent::test_agent_no_holdings -v
tests/test_portfolio_coach.py::TestPortfolioCoachAgent::test_agent_with_holdings PASSED       [ 50%]
tests/test_portfolio_coach.py::TestPortfolioCoachAgent::test_agent_no_holdings PASSED         [100%]
======================================== 2 passed in 16.71s ========================================

# StrategyAgent (2 tests, 0.03s)
$ .\venv\Scripts\python.exe -m pytest tests/test_strategy.py::TestStrategyAgent::test_agent_dividend_strategy tests/test_strategy.py::TestStrategyAgent::test_agent_growth_strategy -v
tests/test_strategy.py::TestStrategyAgent::test_agent_dividend_strategy PASSED                [ 50%]
tests/test_strategy.py::TestStrategyAgent::test_agent_growth_strategy PASSED                  [100%]
======================================== 2 passed in 0.03s =========================================
```

## Agents

Agent overview (Orchestrator + 6 specialized agents):

- **Orchestrator**: Intent routing and agent selection
- **Market Agent**: Real-time quotes and market intel
- **Strategy Agent**: Screeners and investment ideas
- **Portfolio Coach Agent**: Portfolio improvement suggestions
- **Risk Profiler Agent**: Risk assessment from holdings
- **Educator Agent**: Concept explanations via RAG
- **Compliance Agent**: Disclaimers and safe output

The system includes 6 specialized agents (plus Orchestrator) for different financial tasks:

### 1. Educator Agent
**Purpose:** Explain financial concepts using trusted knowledge base

**Module:** `app/agents/educator.py`

**Capabilities:**
- Concept explanation with examples
- Knowledge base retrieval via RAG/TF-IDF
- Beginner-friendly language

**Example:**
```
User: "What is a bond?"
Agent: "A bond is a fixed-income security where you lend money..."
```

### 2. Market Agent
**Purpose:** Provide real-time stock prices and market data

**Module:** `app/agents/market.py`

**Data Source:** Market MCP Server (yFinance)

**Capabilities:**
- Current stock prices
- Percentage change
- Historical data (when requested)
- Multi-ticker support

**Example:**
```
User: "What is the price of AAPL?"
Agent: "AAPL is trading at $180.45 (+2.5%)"
```

### 3. Risk Profiler Agent
**Purpose:** Analyze portfolio risk and volatility

**Module:** `app/agents/risk_profiler.py`

**Data Source:** Portfolio MCP Server

**Capabilities:**
- Portfolio volatility calculation
- Sharpe ratio computation
- Risk assessment
- LLM-powered risk explanation

**Example:**
```
User: "How risky is my portfolio?"
Agent: "Your portfolio has moderate volatility at 18.5%..."
```

### 4. Portfolio Coach Agent
**Purpose:** Analyze portfolio diversification and allocation

**Module:** `app/agents/portfolio_coach.py`

**Data Source:** Portfolio MCP Server

**Capabilities:**
- Allocation analysis (% per holding)
- Concentration detection (>40% single position)
- Diversification scoring (0-100 scale)
- Rebalancing recommendations

**Example:**
```
User: "Is my portfolio well-diversified?"
Agent: "Your portfolio has a diversification score of 75..."
```

### 5. Strategy Agent
**Purpose:** Identify investment opportunities based on strategy type

**Module:** `app/agents/strategy.py`

**Data Source:** Portfolio MCP Server

**Capabilities:**
- Dividend screening & income optimization
- Growth stock identification (top performers)
- Value investing opportunities (bargains)
- Balanced multi-strategy analysis

**Example:**
```
User: "What are my growth opportunities?"
Agent: "Top performers: MSFT (+50%), AAPL (+20%)..."
```

### 6. Compliance Agent
**Purpose:** Apply risk-based safety guardrails

**Module:** `app/agents/compliance.py`

**Capabilities:**
- Risk-based disclaimers
- Advice filtering (blocks HIGH risk)
- Regulatory language enforcement
- PII detection and blocking

**Example:**
```
User: "Should I buy this stock?"
Agent: [Blocks advice for HIGH risk queries]
```

Maintains chat history and context across message turns.

#### Key Capabilities

- **Per-conversation tracking**: Each conversation gets a unique ID
- **Message metadata**: Intent and risk classification stored with each message
- **Context-aware responses**: Recent conversation history auto-passed to LLM agents
- **Automatic persistence**: Conversations saved to `chroma/conversations/` (JSON format)
- **Memory management**: Auto-prunes old messages (keeps 100 most recent per conversation)
- **Singleton pattern**: Single memory instance shared across all requests

#### Usage Example

```powershell
# First message (creates conversation, returns conversation_id)
$headers = @{"Content-Type"="application/json"}
$body = @{"message"="What is a bond?"} | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -Headers $headers -Body $body
$convId = $response.conversation_id

Write-Host "Conversation ID: $convId"
Write-Host "Response: $($response.reply)"

# Follow-up message (uses same conversation for context)
$body = @{
    "message"="How do they work?"
    "conversation_id"=$convId
} | ConvertTo-Json
$response2 = Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -Headers $headers -Body $body
Write-Host "Follow-up Response: $($response2.reply)"
```

#### Response Example

```json
{
  "reply": "A bond is a fixed-income security...",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent": "ASK_CONCEPT",
  "risk": "LOW"
}
```

#### Memory Configuration

In `app/memory.py`:

```python
# Max messages per conversation (older messages auto-pruned)
max_messages_per_conversation=100

# Persistence directory (optional file-based storage)
persist_dir="chroma/conversations"

## Performance Benchmarks (recent)

After recent backend improvements (short-TTL caching, batching + threadpooling of yfinance calls, aggregation cache and optional Redis), we ran integration benchmarks against the running `uvicorn` service. HTTP end-to-end results:

- Small (3 tickers): p50 = 15 ms, p95 = 31 ms, avg = 37 ms
- Medium (6 tickers): p50 = 15 ms, p95 = 32 ms, avg = 53 ms
- Large (20 tickers): p50 = 15 ms, p95 = 31 ms, avg = 65 ms

These numbers are from live HTTP benchmarks executed with `tools/benchmark_market_quote_http.py`. They represent a major improvement over the earlier sequential-yfinance behavior (previously ~1.8s for a 3-ticker request). See `PERFORMANCE_ROADMAP.md` for the full performance plan and progress updates.

Benchmark runner: `tools/benchmark_market_quote_http.py` — outputs `benchmark_market_quote_http_results.json`.

```

#### API Reference

```python
from app.memory import get_memory

memory = get_memory()

# Add message to conversation
memory.add_message(
    conversation_id="uuid",
    role="user",
    content="What is inflation?",
    intent="ASK_CONCEPT",
    risk="LOW"
)

# Get recent messages (formatted for LLM context)
context = memory.get_context(conversation_id, limit=10)

# Clear conversation history
memory.clear_conversation(conversation_id)

# Delete entire conversation
memory.delete_conversation(conversation_id)

# List all conversations
conversations = memory.list_conversations()
```

### 2. AI Gateway

Multi-provider LLM routing with intelligent failover, caching, and resilience.

#### Providers Supported

- **OpenAI** (primary)  GPT-4, GPT-4o-mini, etc.
- **Gemini** (fallback)  Google'"'"'s Gemini models via `google.generativeai`
- **Anthropic** (fallback)  Claude models

#### Key Features

- **Multi-provider failover**: Automatically tries next provider on failure
- **Request caching**: TTL-based cache (3600s default) reduces API calls
- **Circuit breaker**: Temporarily disables failed providers to prevent cascading failures
- **Priority-based routing**: Higher priority providers attempted first
- **Metrics tracking**: Cache hits, failures, active providers
- **Dual support for Gemini**: Uses official GenAI client OR HTTP endpoints

#### Configuration

Set provider API keys in `.env`:

```bash
# Required
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Gemini fallback (choose one method below)
# Method 1: Via google.generativeai client
GEMINI_API_KEY=your-gemini-api-key

# Method 2: Via HTTP endpoint + access token
GEMINI_API_KEY=your-access-token
GEMINI_ENDPOINT=https://generativelanguage.googleapis.com/v1/models/gemini-pro:generate

# Optional: Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Endpoints

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET

# Gateway metrics
Invoke-RestMethod -Uri "http://localhost:8000/metrics" -Method GET
```

#### Metrics Response

```json
{
  "total_requests": 42,
  "cache_hits": 15,
  "cache_hit_rate_percent": 35.71,
  "failures": 2,
  "providers_active": 2
}
```

#### Programmatic Usage

```python
from app.llm import call_llm, get_gateway_metrics

# Call LLM via gateway (auto-routes to available provider)
response = call_llm(
    system_prompt="You are a financial expert.",
    user_prompt="Explain bond pricing.",
    temperature=0.3
)

# Get gateway metrics
metrics = get_gateway_metrics()
print(f"Cache hit rate: {metrics['"'"'cache_hit_rate_percent'"'"']}%")
print(f"Active providers: {metrics['"'"'providers_active'"'"']}")
```

#### Request Flow

```
User Request
    
Cache Check  Cache Hit  Return cached response
     (miss)
Circuit Breaker Check
    
Try Primary Provider (highest priority)
     (success)  Cache response  Return
     (failure)  Record failure
Try Secondary Provider
     (success)  Cache response  Return
     (failure)  Record failure
All providers failed  Raise exception
```

#### Best Practices

- Always configure a primary (OpenAI) and at least one fallback (Gemini or Anthropic)
- Use shorter TTLs for market data (60s) and longer for education content (3600s)
- Monitor `/metrics` endpoint regularly
- Adjust circuit breaker thresholds based on provider reliability
- For Gemini: Use GenAI client if installed, falls back to HTTP endpoint gracefully

### 3. MCP Servers

#### Market MCP Server
Real-time stock quotes via yfinance with MCP-style tools and client wrapper.

**Features:**
- **Live market data**: Fetches current price, change %, currency, timestamp
- **30-second TTL caching**: Reduces API calls for repeated queries
- **Automatic retry**: Graceful fallback on API failures

**Usage:**
```python
from app.mcp.market import get_client

client = get_client()
quote = client.get_quote("AAPL")
print(f"AAPL: ${quote.price} (change: {quote.change_percent}%)")
```

#### Portfolio MCP Server
Portfolio data management with user holdings, transactions, performance tracking, and dividend history.

**Features:**
- **Holdings management**: Current positions with gain/loss calculations
- **Transaction tracking**: Buy, sell, dividend, and transfer events
- **Performance metrics**: Price history, dividend yields, 52-week data
- **User profiles**: Risk tolerance, investment goals, constraints
- **Dividend tracking**: Period-based aggregation and forecasting

**Demo Data Included:**
- Sample user (user_123) with 5-stock portfolio (~$77K value)
- Historical transactions and dividend records
- Performance data with price history

**Usage:**
```python
from app.mcp.portfolio import get_portfolio_client

client = get_portfolio_client("user_123")
holdings = client.get_holdings()
profile = client.get_profile()
transactions = client.get_transactions()
dividends = client.get_dividends()
```

**Database Ready:**
- Hardcoded data now (for development/demo)
- Will connect to PostgreSQL in Phase 2
- SQLAlchemy ORM models ready for implementation

### 4. RAG Engine

TF-IDF-based retrieval over trusted finance knowledge base.

#### Key Decisions

- **TF-IDF** instead of transformers/embeddings  avoids native C++ dependencies
- **Pickle persistence**  lightweight storage at `chroma/embeddings.pkl`
- **Knowledge base**  `data/finance_kb.txt` (can be expanded)

#### Usage

Automatically invoked for education queries:

```powershell
$body = @{"message"="Explain what a stock is"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -Headers $headers -Body $body
```

The educator agent uses RAG to retrieve relevant content from the knowledge base.

### 5. Guardrails

Input validation and output compliance filtering.

- **Input guardrails**: Detects and blocks harmful queries
- **Output guardrails**: Filters LLM responses for compliance
- **Risk classification**: Flags high-risk queries for compliance review

## Project Structure

```
finnie-chat/
 app/
    main.py                 # FastAPI entrypoint with /chat, /health, /metrics
    gateway.py              # Multi-provider LLM gateway (OpenAI, Gemini, Anthropic)
    llm.py                  # LLM client interface (uses gateway)
    memory.py               # Conversation memory with persistence
    intent.py               # Intent classification
    guardrails.py           # Input/output validation
    agents/
       orchestrator.py      # Agent orchestration with context awareness
       educator.py          # Education agent (uses RAG retrieval)
       market.py            # Market data agent (uses Market MCP)
       risk_profiler.py     # Risk analysis agent (uses Portfolio MCP)
       portfolio_coach.py   # Allocation & diversification agent
       strategy.py          # Investment strategy agent (dividend/growth/value)
       compliance.py        # Compliance filtering & safety guardrails
    mcp/
       market_server.py     # Market MCP server (GetQuoteTool via yFinance)
       market.py            # Market client wrapper with 30s caching
       portfolio.py         # Portfolio MCP server (holdings, transactions, etc)
    rag/
        store.py            # TF-IDF vector store
        ingest.py           # Knowledge base ingestion script
 data/
    finance_kb.txt          # Finance knowledge base (text)
 chroma/
    embeddings.pkl          # Persisted TF-IDF embeddings
    conversations/          # Persisted conversation histories (JSON)
 tests/
    conftest.py             # Pytest fixtures
    test_memory.py          # Memory system tests (13 tests)
    test_market.py          # Market MCP tests (8 tests)
    test_gateway.py         # Gateway tests (13 tests)
    test_risk_profiler.py   # Risk Profiler Agent tests (11 tests)
    test_portfolio_coach.py # Portfolio Coach Agent tests (23 tests)
    test_strategy.py        # Strategy Agent tests (20 tests)
    test_portfolio_mcp.py   # Portfolio MCP Server tests (45 tests)
 .env                        # Environment variables (not committed)
 .gitignore
 requirements.txt
 README.md                   # This file
 ARCHITECTURE.md             # Detailed architecture documentation
 GATEWAY.md                  # Detailed gateway documentation
```

## Configuration

### Environment Variables (.env)

```bash
# Required: Primary LLM provider
OPENAI_API_KEY=sk-proj-...

# Optional: Gemini fallback (choose one method below)
# Method 1: Via google.generativeai client
GEMINI_API_KEY=your-api-key

# Method 2: Via HTTP endpoint + access token
GEMINI_API_KEY=your-access-token
GEMINI_ENDPOINT=https://generativelanguage.googleapis.com/v1/models/gemini-pro:generate

# Optional: Anthropic fallback
ANTHROPIC_API_KEY=sk-ant-...
```

### Storage Locations

| Path | Purpose | Format |
|------|---------|--------|
| `.env` | API keys and configuration | Text (key=value) |
| `data/finance_kb.txt` | Finance knowledge base | Text |
| `chroma/embeddings.pkl` | TF-IDF embeddings (cached) | Binary pickle |
| `chroma/conversations/` | Conversation histories | JSON files |

## API Reference

### POST /chat

**Request:**
```json
{
  "message": "What is a bond?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "reply": "A bond is a fixed-income security...",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent": "ASK_CONCEPT",
  "risk": "LOW"
}
```

### GET /health

**Response:**
```json
{
  "status": "ok"
}
```

### GET /metrics

**Response:**
```json
{
  "total_requests": 42,
  "cache_hits": 15,
  "cache_hit_rate_percent": 35.71,
  "failures": 2,
  "providers_active": 2
}
```

## Testing

All test suites are automated with pytest:

```powershell
# Run all tests with coverage
.\venv\Scripts\python.exe -m pytest tests/ -v --cov=app

# Run specific test suite
.\venv\Scripts\python.exe -m pytest tests/test_memory.py -v
.\venv\Scripts\python.exe -m pytest tests/test_market.py -v
.\venv\Scripts\python.exe -m pytest tests/test_gateway.py -v

# Run with verbose output
.\venv\Scripts\python.exe -m pytest tests/ -vv
```

## Deployment

### Local Development

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Production

```powershell
# Use gunicorn (install: pip install gunicorn)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `openai` | OpenAI API client |
| `google-generativeai` | Google Gemini client (optional) |
| `anthropic` | Anthropic Claude client (optional) |
| `yfinance` | Stock data API |
| `scikit-learn` | TF-IDF vectorization |
| `pytest` | Testing framework |

## Known Limitations & Future Enhancements

### Current Limitations

1. **Single-user**: No built-in authentication or multi-user isolation
2. **In-memory + file storage**: For scalable deployments, consider database (PostgreSQL, MongoDB)
3. **Gemini HTTP mode**: Requires proper endpoint + token configuration
4. **TF-IDF RAG**: Lighter than transformers but less semantic

### Planned Enhancements

- [ ] User authentication and session management
- [ ] Database-backed conversation storage
- [ ] Advanced RAG with semantic embeddings (with optional torch)
- [ ] Streaming responses for long-form content
- [ ] Rate limiting and quota management
- [ ] Audit logging and compliance reporting
- [ ] Multi-language support

## Troubleshooting

### Issue: "All LLM providers failed"

**Cause**: No valid provider configured or all providers down

**Solution**:
```powershell
# Check /metrics endpoint
Invoke-RestMethod -Uri "http://localhost:8000/metrics" -Method GET

# Verify .env has at least OPENAI_API_KEY set
cat .env | Select-String "OPENAI_API_KEY"
```

### Issue: Low cache hit rate

**Cause**: Unique queries, short TTL, or caching disabled

**Solution**:
- Reuse common system prompts
- Increase cache TTL in `app/gateway.py`
- Monitor with `/metrics` endpoint

### Issue: Conversation not persisting

**Cause**: `chroma/conversations/` directory missing or permissions denied

**Solution**:
```powershell
# Create directory if missing
New-Item -ItemType Directory -Path "chroma/conversations" -Force

# Check file permissions
Get-Item "chroma/conversations" | Format-List
```

## Contributing

1. Create a branch: `git checkout -b feature/my-feature`
2. Make changes and test: `pytest tests/`
3. Commit: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Create a Pull Request

## License

MIT License  see LICENSE file for details

## Support

For issues, questions, or feature requests, open an issue on GitHub or contact the maintainers.
