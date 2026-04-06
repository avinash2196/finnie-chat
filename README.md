![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-453%20passed-brightgreen?logo=pytest&logoColor=white)
![DeepEval](https://img.shields.io/badge/DeepEval-12%20tests-blueviolet)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

# Finnie Chat — Multi-Agent Financial AI

> A production-oriented financial assistant where an LLM orchestrator routes questions across **9 specialized agents** — each with its own data source, retrieval layer, and compliance guardrails. Built to demonstrate real system design, not just prompt engineering.

Covers: portfolio analysis · live market quotes · concept education (RAG) · goal planning · tax concepts · news synthesis · risk profiling · strategy screening · compliance filtering.

---

## Why This Architecture?

Most AI chatbot demos use a single model with a system prompt. Finnie Chat is different: intent classification determines the domain, a planner LLM assembles the right agent pipeline, and each agent accesses appropriate data sources (live market quotes, relational database holdings, a curated knowledge base). The result handles concept explanations, real-time prices, portfolio risk, investment screening, and news — all in one conversation — with compliance guardrails on every response.

---

## Project Status

| Capability | Status |
|---|---|
| 9-agent LLM orchestration | ✅ Functional |
| Multi-provider LLM gateway (OpenAI → Gemini → Anthropic) | ✅ Functional |
| Hybrid RAG engine (TF-IDF + sentence-transformers) | ✅ Functional |
| SQLAlchemy database layer (SQLite dev / PostgreSQL prod) | ✅ Functional |
| Streamlit frontend (Chat, Portfolio, Market, About) | ✅ Functional |
| Observability — LangSmith + Arize AI | ✅ Optional; safe no-ops without keys |
| DeepEval LLM test suite (12 tests) | ✅ All passing; ExactMatch-based, fully mocked |
| Test suite | ✅ 453 passed |
| Portfolio MCP server | ⚠️ Agents use mock data; DB-backed variant built, not yet wired |
| Alembic migrations | ⚠️ Dependency present; migration files not yet configured |

---

## Architecture

```
User Message
    |
    +-- Input Guardrails (PII / blocked-word check)
    |
    +-- Conversation Memory (inject recent history as context)
    |
    +-- Intent Classifier (LLM + rule-based fallback)
    |     ASK_CONCEPT | ASK_MARKET | ASK_PORTFOLIO | ASK_RISK
    |     ASK_STRATEGY | ASK_GOAL | ASK_NEWS | ASK_TAX | ADVICE | OTHER
    |
    +-- Orchestrator (LLM planner selects agent pipeline)
          |
          +-- EducatorAgent        <- Hybrid RAG (TF-IDF + sentence-transformers)
          +-- MarketAgent          <- Market MCP Server (yFinance, short-TTL cache)
          +-- RiskProfilerAgent    <- Portfolio MCP Server
          +-- PortfolioCoachAgent  <- Portfolio MCP Server
          +-- StrategyAgent        <- Market MCP Server (dividend / growth / value)
          +-- GoalPlanningAgent    <- LLM reasoning over user goals
          +-- NewsSynthesizerAgent <- News MCP Server (Alpha Vantage)
          +-- TaxEducationAgent    <- LLM + knowledge base
          +-- ComplianceAgent      <- Always last; adds risk-based disclaimers
                |
                +-- AI Gateway (OpenAI primary -> Gemini -> Anthropic fallback)
                      +-- In-memory response cache (TTL-based)
                      +-- Circuit breaker per provider
                      +-- LangSmith tracing (optional, safe no-op without key)

Database Layer  (SQLAlchemy -- SQLite dev / PostgreSQL prod)
    +-- User, Holding, Transaction, PortfolioSnapshot, SyncLog models
    +-- Background portfolio sync (SyncTaskRunner, hourly)
    +-- Provider pattern: MockPortfolioProvider | RobinhoodPortfolioProvider | FidelityPortfolioProvider

Observability   (both optional, safe no-ops without keys)
    +-- LangSmith -- hierarchical run traces (intent -> router -> agents -> composer)
    +-- Arize AI  -- prediction logging, quality signals, safety tags
```

---

## Key Components

| Module | Path | Role |
|---|---|---|
| FastAPI app | `app/main.py` | REST API, middleware, DB init |
| Orchestrator | `app/agents/orchestrator.py` | LLM-based agent planner |
| Intent classifier | `app/intent.py` | LLM classifier + deterministic fallback |
| AI Gateway | `app/gateway.py` | Multi-provider LLM client with circuit breaker |
| RAG engine | `app/rag/` | Hybrid TF-IDF + semantic retrieval, Protocol-based |
| Market MCP | `app/mcp/market_server.py` | yFinance wrapper with batching & TTL cache |
| Portfolio MCP | `app/mcp/portfolio.py` | Mock-data MCP server used by agents (DB-backed variant: `app/portfolio_mcp_db.py`) |
| News MCP | `app/mcp/news_server.py` | Alpha Vantage news with ticker filtering |
| Database | `app/database.py` | SQLAlchemy ORM, 5 models |
| Providers | `app/providers.py` | Abstract provider pattern for portfolio sync |
| Observability | `app/observability.py` | LangSmith + Arize integration |
| Guardrails | `app/guardrails.py` | Input PII check, output risk-level filtering |
| Memory | `app/memory.py` | JSON-persisted conversation history |
| Streamlit UI | `frontend/` | 4-page app: Chat, Portfolio, Market, About |

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2, Alembic |
| Frontend | Streamlit (4 pages) |
| LLM / Agents | OpenAI, LangChain, LangGraph, LangSmith |
| LLM Fallbacks | Google Gemini, Anthropic (gateway-managed) |
| RAG | scikit-learn (TF-IDF), sentence-transformers |
| Market Data | yFinance, Alpha Vantage (via MCP servers) |
| Database | SQLite (dev), PostgreSQL (prod) |
| Observability | LangSmith, Arize AI |
| Caching | In-memory (TTL-based) + optional Redis |
| Testing | pytest, pytest-asyncio, DeepEval |

---

## Key Features

### Nine Specialized Agents

Each agent is a distinct Python module with a focused capability set:

- **EducatorAgent** -- explains financial concepts using hybrid RAG retrieval over `data/finance_kb.txt` with source attribution and confidence scoring
- **MarketAgent** -- fetches live quotes via yFinance; supports multi-ticker batching and a short-TTL aggregation cache
- **RiskProfilerAgent** -- computes portfolio volatility, Sharpe ratio, and concentration risk from holdings
- **PortfolioCoachAgent** -- analyses diversification (0-100 scoring), detects high single-position concentration, recommends rebalancing
- **StrategyAgent** -- screens for dividend, growth, and value opportunities; exposes dedicated screener endpoints
- **GoalPlanningAgent** -- extracts savings targets, suggests milestones and monthly contribution estimates
- **NewsSynthesizerAgent** -- queries Alpha Vantage with ticker-specific and general market news; 3-tier fallback pipeline with a COMMON_WORDS filter to prevent false ticker extraction
- **TaxEducationAgent** -- covers tax-advantaged accounts (IRA, Roth, 401k), capital gains treatment, and tax-loss harvesting basics
- **ComplianceAgent** -- always runs last; applies risk-based disclaimers and blocks HIGH-risk direct advice

### Intent-Driven Routing

`app/intent.py` classifies every message into one of ten intents with a LOW / MED / HIGH risk label. An LLM-based classifier runs first; a deterministic keyword fallback activates when the LLM is unavailable, keeping the system functional without a live API key during tests and local development.

### Hybrid RAG Engine

`app/rag/` provides a Protocol-based `Retriever` abstraction with three concrete backends:

- **HybridRetriever** -- blends TF-IDF and sentence-transformers cosine scores using `all-MiniLM-L6-v2` (384-dim)
- **TFIDFRetriever** -- scikit-learn vectorizer, no GPU dependency
- **SemanticRetriever** -- sentence-transformers only

Model loading is lazy (downloaded on first use). Retrieved passages include similarity scores and source attribution that surface in agent responses.

### Multi-Provider AI Gateway

`app/gateway.py` supports OpenAI (primary), Google Gemini, and Anthropic (fallbacks). Features:

- Priority-based provider ordering
- TTL-based in-memory response cache to reduce redundant API calls
- Per-provider circuit breaker that temporarily disables a failing provider
- Metrics endpoint (`GET /metrics`) reporting cache-hit rate, failure count, and active providers

### Database-Backed Portfolio Management

Five SQLAlchemy models (User, Holding, Transaction, PortfolioSnapshot, SyncLog) backed by SQLite in development and PostgreSQL in production (via `DATABASE_URL` env var). A provider-pattern abstraction (`MockPortfolioProvider`, `RobinhoodPortfolioProvider`, `FidelityPortfolioProvider`) allows switching data sources without code changes. A background `SyncTaskRunner` handles periodic portfolio refresh.

> Note: agents currently call `app/mcp/portfolio.py`, which uses hardcoded demo data. `app/portfolio_mcp_db.py` contains a DB-integrated MCP server variant that wires into the SQLAlchemy layer.

### Observability

Both LangSmith and Arize AI integrations are optional and implemented as safe no-ops when API keys are absent. When enabled:

- **LangSmith** receives a hierarchical run tree: intent -> router -> per-agent spans -> final composer
- **Arize AI** receives prediction logs with quality metrics (groundedness, retrieval relevance, hallucination risk) and safety tags (PII detected, restricted advice triggered)

---

## Quick Start

### Prerequisites

- Python 3.11+
- An OpenAI API key (minimum; Gemini and Anthropic keys optional for fallback)

### Install

```bash
git clone https://github.com/avinash2196/finnie-chat.git
cd finnie-chat

python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Streamlit is used by the frontend but is not in requirements.txt; install it separately:
pip install streamlit
```

### Configure

```bash
# Minimum viable .env
echo "OPENAI_API_KEY=sk-proj-..." > .env

# Optional fallback providers
echo "GEMINI_API_KEY=your-key" >> .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Optional observability
echo "LANGSMITH_API_KEY=lsv2_pt_..." >> .env
echo "LANGSMITH_PROJECT=finnie-chat" >> .env
echo "ARIZE_API_KEY=your-arize-key" >> .env
echo "ARIZE_SPACE_KEY=your-space-key" >> .env
```

### Initialise the database

```bash
python -c "from app.database import init_db; init_db()"
```

### Run

```bash
# macOS / Linux  starts backend (port 8000) and frontend (port 8501)
./start.sh

# Windows
.\start.bat

# Or start services individually
uvicorn app.main:app --port 8000 --reload
streamlit run frontend/Home.py
```

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501

---

## API Usage Examples

### Chat (single turn)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is a Roth IRA?", "user_id": "user_001"}'
```

```json
{
  "reply": "A Roth IRA is funded with after-tax dollars...",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent": "ASK_TAX",
  "risk": "MED"
}
```

### Multi-turn conversation

```bash
# Pass conversation_id to maintain context across turns
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How does it compare to a traditional IRA?",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_001"
  }'
```

### Market quote

```bash
curl -X POST http://localhost:8000/market/quote \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL"]}'
```

### Portfolio analytics

```bash
curl http://localhost:8000/users/user_001/analytics
```

### Gateway metrics

```bash
curl http://localhost:8000/metrics
```

```json
{
  "total_requests": 42,
  "cache_hits": 15,
  "cache_hit_rate_percent": 35.7,
  "failures": 2,
  "providers_active": 2
}
```

### Observability status

```bash
curl http://localhost:8000/observability/status
```

---

## Testing

The `tests/` directory contains unit, integration, and LLM-evaluation tests across subdirectories (`unit/`, `integration/`, `deepeval/`, `manual/`).

```bash
# Full suite
pytest tests/ -v

# Quiet
pytest tests/ -q

# Specific module
pytest tests/test_gateway.py -v
pytest tests/test_rag.py -v
pytest tests/test_database.py -v

# Parallel
pytest tests/ -n auto

# Include manual / integration tests
RUN_MANUAL_TESTS=1 pytest tests/ -v

# LLM-eval quality tests (DeepEval  requires live keys)
pytest tests/deepeval/ -v
```

Key test areas:

| Area | Representative files |
|---|---|
| Gateway & LLM routing | `test_gateway.py` |
| Agent behaviour | `test_educator_agent.py`, `test_market_agent.py`, `test_risk_profiler.py`, `test_portfolio_coach.py`, `test_strategy.py`, `test_goal_planning.py`, `test_news_synthesizer.py`, `test_tax_education.py`, `test_compliance_agent.py` |
| RAG retrieval | `test_rag.py`, `test_retriever_abstraction.py`, `test_semantic_search.py` |
| Database & sync | `test_database.py`, `test_integration_sync.py`, `test_portfolio_mcp_database.py` |
| Observability | `test_observability.py`, `test_observability_langsmith.py` |
| Intent & guardrails | `test_intent_extra.py`, `test_guardrails.py` |

---

## Further Reading

| Document | When to read it |
|---|---|
| [Architecture & Data Flow](docs/architecture/ARCHITECTURE.md) | Full request pipeline, agent coordination, flowcharts |
| [AI Gateway](docs/architecture/GATEWAY.md) | LLM routing, circuit-breaker, caching, provider config |
| [Database Guide](docs/architecture/DATABASE_GUIDE.md) | SQLAlchemy models, provider pattern, DB-backed MCP variant |
| [Executive Summary](docs/summaries/EXECUTIVE_SUMMARY.md) | One-page overview — what is built and what is still open |
| [Test Coverage](docs/testing/TEST_COVERAGE.md) | Per-module breakdown of all 452 tests |
| [Quick Start (Windows)](docs/implementation/QUICK_START.md) | Step-by-step startup walkthrough |
| [Documentation Index](docs/DOCUMENTATION_INDEX.md) | Full index of all project docs |
| LLM quality (DeepEval) | `tests/deepeval/` |

> All observability integrations are safe no-ops in testsno live LangSmith or Arize keys are required to run the suite.

---

## Repo Structure

```
finnie-chat/
 app/
    main.py                # FastAPI app, all endpoints, middleware
    gateway.py             # Multi-provider LLM gateway
    intent.py              # Intent classification (LLM + rule-based fallback)
    memory.py              # JSON-persisted conversation history
    database.py            # SQLAlchemy models and session factory
    providers.py           # Portfolio provider pattern (Mock/Robinhood/Fidelity)
    sync_tasks.py          # Background portfolio sync scheduler
    observability.py       # LangSmith + Arize integration
    guardrails.py          # Input PII check, output risk-level filter
    agents/
       orchestrator.py    # LLM planner + agent dispatch
       educator.py
       market.py
       risk_profiler.py
       portfolio_coach.py
       strategy.py
       compliance.py
       goal_planning.py
       news_synthesizer.py
       tax_education.py
    mcp/
       market_server.py   # yFinance MCP server
       market.py          # Market client wrapper
       portfolio.py       # Portfolio MCP server
       news_server.py     # Alpha Vantage news MCP server
       news.py            # News client wrapper
    rag/
        store.py           # Vector store (TF-IDF + semantic)
        retriever.py       # Protocol-based retriever abstraction
        ingest.py          # Knowledge base ingestion
        verification.py   # Retrieval scoring + source attribution
 frontend/
    Home.py                # Streamlit entry point (Chat page)
    pages/
        0__Chat.py
        1__Portfolio.py
        2__Market.py
        3_ℹ_About.py
 data/
    finance_kb.txt         # Curated financial knowledge base
 tests/                     # pytest suite (unit / integration / deepeval / manual)
 deploy/                    # systemd unit files + startup helper scripts
 scripts/                   # DB utilities, RAG improvement scripts
 tools/                     # Benchmarking and profiling utilities
 docs/                      # Architecture diagrams, implementation notes
 requirements.txt
 start.sh / start.bat       # One-command startup (backend + frontend)
 pytest.ini
```

---

## Roadmap

Items tracked in `docs/planning/` and `docs/PERFORMANCE_ROADMAP.md`:

- Streaming responses for long-form agent output
- PostgreSQL as default persistence (alembic is a listed dependency; migration files not yet scaffolded)
- Rate limiting and per-user quota management
- Extended LLM-evaluation coverage via DeepEval
- User authentication and session isolation

---

## What Makes This Stand Out

**Architectural discipline over demo code.** The system separates concerns cleanly: intent classification, agent selection, data retrieval, LLM inference, and observability each live in their own module with defined interfaces. The retriever is a Protocol type -- swap backends without touching calling code. The gateway is a standalone component -- swap providers without touching agents.

**Resilience by design.** The LLM gateway has per-provider circuit breakers, retries, and a TTL cache. The observability layer degrades gracefully to no-ops. The intent classifier has a deterministic fallback so the system routes correctly even without a live LLM.

**Testability.** The test directory covers individual agents, the RAG pipeline, database integration, observability decorators, and LLM-evaluation quality metrics via DeepEval. Observability and external services are mock-safe -- the suite runs locally without live API keys.

**Real data layer.** SQLAlchemy ORM (with Alembic as a listed dependency for future migrations), a provider abstraction for portfolio data sources, and a background sync scheduler -- not toy in-memory dictionaries.

---

## License

MIT -- see `LICENSE` for details.

## Known Limitations

- Portfolio MCP currently uses mock data (DB-backed variant not yet integrated)
- Alembic migrations not yet configured
- RAG uses TF-IDF + embeddings (not vector DB-backed yet)