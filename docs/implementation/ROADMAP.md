# Finnie-Chat: Development Roadmap

> **Archived — project delivered December 2025.** All five phases are complete. This file is retained as a build record; it does not describe current functionality. For the current system, see `README.md` and `docs/architecture/ARCHITECTURE.md`.

---

## Delivered Phases

### Phase 1 — Backend Core
- FastAPI application with all endpoints and middleware
- Multi-provider LLM gateway (OpenAI primary; Gemini and Anthropic fallback) with circuit breaker and TTL cache
- Intent classifier (LLM + deterministic fallback)
- Conversation memory (JSON-persisted)
- Input/output guardrails (PII detection, risk-level filtering)

### Phase 2 — Frontend MVP
- Streamlit multipage app: Chat (`Home.py`), Portfolio (`1_📊_Portfolio.py`), Market (`2_📈_Market.py`), About (`3_ℹ️_About.py`)
- Chat tab with session state and user-ID support
- Connected to FastAPI backend via REST (`/chat`, `/market/quote`, portfolio endpoints)

### Phase 3 — Portfolio System
- SQLAlchemy ORM with five models: User, Holding, Transaction, PortfolioSnapshot, SyncLog
- Provider pattern: MockPortfolioProvider, RobinhoodPortfolioProvider, FidelityPortfolioProvider
- Background hourly sync scheduler (`app/sync_tasks.py`)
- Full portfolio REST API: create user, add/list holdings, sync, analytics, allocation, performance
- Portfolio tab: Holdings, Allocation, Transactions, Performance, Manage sub-tabs

### Phase 4 — Market Trends System
- Market MCP server (`app/mcp/market_server.py`) with yFinance batching and per-ticker parallelism
- Short-TTL aggregation cache for `/market/quote`; optional Redis fallback via `REDIS_URL`
- Strategy Agent: dividend, growth, and value screeners
- Market Trends page: Overview, Screeners, Strategy Ideas, Sector Analysis

### Phase 5 — Observability and Test Hardening
- LangSmith tracing  hierarchical runs (intent -> router -> agents -> composer); optional, safe no-op without key
- Arize AI logging  quality and safety signals; optional
- Test suite: 452 passed, 1 known failure (`tests/test_rag.py::test_rag_grounded_answer`)
- DeepEval LLM-quality tests in `tests/deepeval/`
- systemd unit files and startup scripts in `deploy/`

---

## Nine Specialized Agents (all delivered)

| Agent | Module | Capability |
|---|---|---|
| Orchestrator | `app/agents/orchestrator.py` | LLM-based planner; dispatches agent pipeline |
| Educator | `app/agents/educator.py` | RAG retrieval over finance knowledge base |
| Market | `app/agents/market.py` | Live quotes via yFinance MCP |
| Risk Profiler | `app/agents/risk_profiler.py` | Volatility, Sharpe ratio, concentration risk |
| Portfolio Coach | `app/agents/portfolio_coach.py` | Allocation analysis, diversification scoring |
| Strategy | `app/agents/strategy.py` | Dividend, growth, and value screeners |
| Goal Planning | `app/agents/goal_planning.py` | Savings goals, SIP calculations, milestones |
| News Synthesizer | `app/agents/news_synthesizer.py` | Alpha Vantage news with ticker filtering |
| Tax Education | `app/agents/tax_education.py` | Tax-advantaged accounts, capital gains concepts |
| Compliance | `app/agents/compliance.py` | Deterministic post-filter; always last |

---

## Open Items

- **Portfolio MCP -> database:** `app/portfolio_mcp_db.py` (SQLAlchemy-backed) is built and tested. Agents currently import `app/mcp/portfolio.py` (mock data). Replacing the import in each agent is the only wiring step.
- **Alembic migrations:** `alembic` is a listed dependency. Migration files are not yet scaffolded.
- **Redis cache:** In-memory TTL cache is active. Redis support is wired via optional `REDIS_URL` but not deployed.
- **OTel tracing:** `instrument_*` methods are intentional no-ops in the current release. Grafana dashboards deferred.
- **DeepEval expansion:** Coverage target >= 90%; currently 452/453 non-DeepEval tests pass.
