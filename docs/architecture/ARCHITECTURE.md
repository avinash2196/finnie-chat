# Finnie-Chat: Architecture & Data Flow

## System Overview

Finnie-Chat is a sophisticated financial AI system with an Orchestrator plus 9 specialized agents that process user questions through a multi-layered reasoning and synthesis pipeline, combining intent classification, portfolio analysis, market data, and safety guardrails.

**Current State:** Portfolio MCP server (`app/mcp/portfolio.py`) currently uses hardcoded mock data. A database-backed implementation exists in `app/portfolio_mcp_db.py` but is not yet integrated into the agent pipeline.

---

## Presentation-Ready Diagram

An up-to-date, presentation-ready architecture diagram is available here:

- [Architecture Diagram (SVG)](architecture_diagram.svg)

This diagram highlights the recent production-ready improvements:

- MCP batching and per-ticker parallelism for lower latency
- Short-TTL aggregation cache (`_quote_agg_cache`) with optional Redis fallback (`REDIS_URL`)
- FastAPI timing middleware and observability instrumentation (LangSmith + Arize safe no-op)
- Streamlit frontend calling the backend endpoints (Chat, Market, Portfolio)

See the "Developer Notes" section below for quick pointers on running tests and generating profiling artifacts.


## Complete Request Flow (Portfolio Data Integration)

```
User Query with User ID (e.g., /chat?user_id=user_002)
   │
   ▼ Intent Classification + Risk Assessment
   │
   ▼ Orchestrator (passes user_id to agents)
   │
   ├─ [Educator Agent] ◄─ RAG (TF-IDF) Knowledge Base
   ├─ [Market Agent] ◄─ Market MCP Server (yFinance)  
   ├─ [Risk Profiler Agent] ◄─ Portfolio MCP Server (mock data)
   │                            • get_user_holdings(user_id)
   │
   ├─ [Portfolio Coach Agent] ◄─ Portfolio MCP Server (mock data)
   │                             • get_user_profile(user_id)
   │                             • get_transaction_history()
   │
   ├─ [Strategy Agent] ◄─ Portfolio MCP Server (mock data)
   │                       • DB-backed variant: app/portfolio_mcp_db.py (not yet wired)
   │
   └─ [Compliance Agent] ◄─ Safety Rules
       • Risk-based disclaimers
       • No duplicates (Dec 2025 fix)
   │
   ▼ LLM Synthesis Layer
   │
   ▼ Output Guardrails + Compliance
   │
   ▼ Final Response + Memory Storage
```

## Portfolio Data Layer

**Active implementation:** `app/mcp/portfolio.py` — hardcoded mock holdings, used by all portfolio-related agents (Risk Profiler, Portfolio Coach, Strategy).

**Database-backed variant:** `app/portfolio_mcp_db.py` — SQLAlchemy-backed implementation that queries the live `Holding` table. Not yet imported by agents; replacing the mock import in each agent is the only wiring step required.

## Complete Request Flowchart

```
User Query
   │
   ▼
┌─────────────────────────────────────────┐
│   Backend API (FastAPI)                 │
│   POST /chat                            │
│   ├─ message: "What stocks do I own?"   │
│   ├─ user_id: "user_002"                │
│   └─ conversation_id: "conv_123"        │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│   INPUT GUARDRAILS                      │
│   ────────────────────────────          │
│   • PII Detection (SSN, account #)      │
│   • Unsafe Input Blocking               │
│   • Message Validation                  │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│   LLM REASONING LAYER                   │
│   ────────────────────────────          │
│   Uses: app/llm.py → OpenAI GPT-4o-mini│
│                                         │
│   Processes:                            │
│   • Intent Classification               │
│   • Risk Assessment                     │
│   • Agent Selection                     │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│   INTENT CLASSIFICATION                 │
│   ────────────────────────────          │
│   Module: app/intent.py                 │
│                                         │
│   Returns:                              │
│   • Intent: ASK_CONCEPT | ASK_MARKET    │
│   • Risk Level: LOW | MED | HIGH        │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│   ORCHESTRATOR                          │

│   ────────────────────────────          │
│   Module: app/agents/orchestrator.py    │
│                                         │
│   Dispatches to appropriate agents      │
│   based on intent                       │
└─────────────────────────────────────────┘
   │
   ├─────────────────────────┬──────────────────────────┐
   │                         │                          │
   ▼                         ▼                          ▼
┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│ EDUCATOR AGENT   │  │ MARKET AGENT     │  │ PORTFOLIO AGENTS    │
│ ────────────────│  │ ────────────────│  │ ────────────────────│
│ Module:         │  │ Module:         │  │ RiskProfilerAgent   │
│ app/agents/     │  │ app/agents/     │  │ PortfolioCoachAgent │
│ educator.py     │  │ market.py       │  │ StrategyAgent       │
│                 │  │                 │  │ GoalPlanningAgent   │
│ Data Source:    │  │ Data Source:    │  │ NewsSynthesizer     │
│ • RAG Engine    │  │ • yFinance API  │  │ TaxEducationAgent   │
│ • TF-IDF        │  │ • Market MCP    │  │                     │
│   Embeddings    │  │   Server        │  │ Data Source:        │
│ • Finance KB    │  │                 │  │ • Portfolio MCP     │
│   (TF-IDF pkl)  │  │ Returns:        │  │   (mock data)       │
│                 │  │ • Price         │  │ • Market MCP        │
│ Returns:        │  │ • % Change      │  │ • LLM reasoning     │
│ • Explanation   │  │ • Currency      │  └─────────────────────┘
│ • Concepts      │  │ • Error msgs    │
│ • Examples      │  │                 │
└──────────────────┘  └──────────────────┘
   │                         │                          │
   └─────────────────────────┼──────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────┐
│   LLM SYNTHESIS LAYER                   │
│   ────────────────────────────          │
│   Uses: app/llm.py → OpenAI GPT-4o-mini│
│                                         │
│   Combines agent outputs:               │
│   • Merges multiple agent responses     │
│   • Synthesizes coherent answer         │
│   • Explains in simple language         │
│   • Ensures facts match agent data      │
│   • NO invented information             │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│   OUTPUT GUARDRAILS                     │
│   ────────────────────────────          │
│   Module: app/guardrails.py             │
│                                         │
│   Enforcement:                          │
│   • Advice Blocking (HIGH risk)         │
│   • Tone Enforcement                    │
│   • Safety Validation                   │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│   COMPLIANCE AGENT                      │
│   ────────────────────────────          │
│   Module: app/agents/compliance.py      │
│                                         │
│   Deterministic Post-Filter:            │
│   • Risk-based disclaimers              │
│   • MED risk: Add warnings              │
│   • HIGH risk: Block advice             │
│   • Add regulatory language             │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│   FINAL RESPONSE                        │
│   ────────────────────────────          │
│   {                                     │
│     "reply": "Your answer...",          │
│     "intent": "ASK_CONCEPT",            │
│     "risk": "LOW"                       │
│   }                                     │
└─────────────────────────────────────────┘
```

---

## Agent Details

### Orchestrator
**Purpose:** Route requests to appropriate agents based on intent and context

**Module:** `app/agents/orchestrator.py`

**Responsibilities:**
- Intent-aware agent selection
- Aggregating multi-agent outputs
- Fallback logic and graceful degradation

### 1. Educator Agent
**Purpose:** Explain financial concepts using trusted knowledge base

**Module:** `app/agents/educator.py`

**Data Source:** 
- RAG Engine (`app/rag/store.py`)
- TF-IDF Embeddings (scikit-learn) + sentence-transformers (all-MiniLM-L6-v2)
- Pickle-based cache (`chroma/embeddings.pkl`) — not a ChromaDB database
- Finance Knowledge Base (`data/finance_kb.txt`)

### 2. Market Agent
**Purpose:** Fetch live market data and stock prices

**Module:** `app/agents/market.py`

**Data Source:**
- yFinance API via Market MCP Server (`app/mcp/market.py`)
- Short-TTL aggregation cache for repeated queries

### 3. Risk Profiler Agent
**Purpose:** Compute portfolio volatility, Sharpe ratio, and concentration risk

**Module:** `app/agents/risk_profiler.py`

**Data Source:** Portfolio MCP Server (mock data; see Portfolio Data Layer section above)

### 4. Portfolio Coach Agent
**Purpose:** Analyse diversification (0–100 scoring), detect concentration, suggest rebalancing

**Module:** `app/agents/portfolio_coach.py`

**Data Source:** Portfolio MCP Server (mock data)

### 5. Strategy Agent
**Purpose:** Screen for dividend, growth, and value opportunities

**Module:** `app/agents/strategy.py`

**Data Source:** Market MCP Server

### 6. Goal Planning Agent
**Purpose:** Extract savings targets, suggest milestones and monthly contribution estimates

**Module:** `app/agents/goal_planning.py`

### 7. News Synthesizer Agent
**Purpose:** Query Alpha Vantage for ticker-specific and general market news; 3-tier fallback

**Module:** `app/agents/news_synthesizer.py`

**Data Source:** News MCP Server (`app/mcp/`)

### 8. Tax Education Agent
**Purpose:** Cover tax-advantaged accounts (IRA, Roth, 401k), capital gains, tax-loss harvesting

**Module:** `app/agents/tax_education.py`

### 9. Compliance Agent
**Purpose:** Deterministic safety filtering — always runs last

**Module:** `app/agents/compliance.py`

**Rules:**
- **LOW risk:** Pass through unchanged
- **MED risk:** Add warning disclaimers (deduplication applied)
- **HIGH risk:** Block direct advice

---

## Implementation Notes (2025‑12‑26)

- **Observability:** LangSmith runs are created/updated synchronously; Arize logging is optional; OTEL instrumentation is not active and `instrument_*` methods are no‑ops.
- **Gateway:** In test environments the circuit breaker prevents outbound LLM calls; agent outputs are synthesized deterministically or via mocks.
- **Caching:** Short‑TTL aggregation cache is enabled in `app/main.py`; Redis fallback is optional via `REDIS_URL`.

## Key Components

| Component | File | Purpose |
|-----------|------|---------|
| **Main App** | `app/main.py` | FastAPI entry point, .env loading |
| **LLM Client** | `app/llm.py` | OpenAI GPT-4o-mini wrapper (lazy-loaded) |
| **Intent Router** | `app/intent.py` | Classify message intent & risk |
| **Orchestrator** | `app/agents/orchestrator.py` | Dispatch to agents |
| **Guardrails** | `app/guardrails.py` | Input/output safety filters |
| **RAG Store** | `app/rag/store.py` | TF-IDF embeddings & retrieval |
| **RAG Ingest** | `app/rag/ingest.py` | Load knowledge base |
| **Market API** | `app/mcp/market.py` | yFinance integration |

---

## Testing & Quality

Finnie Chat uses a two-layer test strategy:

- **pytest unit/integration suite** (`tests/`) — 453 tests covering agent logic, API endpoints, RAG retrieval, guardrails, memory, and observability. All LLM calls are intercepted by a circuit-breaker in test environments so no external keys are required.
- **DeepEval LLM quality suite** (`tests/deepeval/`) — 12 deterministic tests using [DeepEval](https://github.com/confident-ai/deepeval)'s `ExactMatchMetric`. Each test mocks the LLM/MCP layer and asserts the exact expected output through `evaluate()`, covering: market price formatting (`MarketAgent`), RAG-grounded educator responses, strategy/portfolio-coach/risk-profiler synthesis, orchestrator intent routing, and portfolio context isolation per user.

| File | Tests | Coverage |
|---|---|---|
| `test_deepeval_paths.py` | 2 | `MarketAgent` price format, `EducatorAgent` RAG grounding |
| `test_deepeval_other_agents.py` | 4 | Strategy, PortfolioCoach, RiskProfiler, Orchestrator routing |
| `test_deepeval_portfolio_chat.py` | 6 | Portfolio context access, user isolation, diversification, risk, compliance wording |

Run DeepEval tests:
```bash
python -m pytest tests/deepeval/ -v --no-cov
```

---

## Data Sources & External Integrations

### 1. LLM: OpenAI GPT-4o-mini
- **Environment Variable:** `OPENAI_API_KEY` (loaded from `.env`)
- **Usage:** Reasoning + Synthesis layers
- **Model:** `gpt-4o-mini` (cost-efficient)

### 2. Market Data: yFinance
- **Python Package:** `yfinance`
- **Data:** Stock prices, % change, currency
- **No auth required** (public API)

### 3. Knowledge Base: TF-IDF + sentence-transformers (pickle-based storage)
- **Storage:** `chroma/embeddings.pkl` (pickle file, not a ChromaDB database)
- **Content:** `data/finance_kb.txt`
- **Embedding Method:** TF-IDF (scikit-learn) with sentence-transformers semantic fallback
- **No external auth** (local file storage)

---

## Environment Setup

### Required Files

1. **`.env`** (project root)
   ```
   OPENAI_API_KEY=sk-proj-...your-key...
   ```

2. **`data/finance_kb.txt`** (financial knowledge base)
   - Contains: ETF definitions, stock concepts, diversification, etc.
   - Used by RAG for educational queries

3. **`chroma/embeddings.pkl`** (generated by ingest)
   - Auto-created by `python app/rag/ingest.py`
   - Persists embeddings across restarts

### Setup Commands

```bash
# 1. Install dependencies (already done)
.\venv\Scripts\python.exe -m pip install fastapi uvicorn openai yfinance scikit-learn

# 2. Load knowledge base into RAG
.\venv\Scripts\python.exe app/rag/ingest.py

# 3. Start the server
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

---

## API Endpoint

### POST /chat

**Request:**
```json
{
  "message": "What is diversification?"
}
```

**Response:**
```json
{
  "reply": "Here's a simple explanation: Diversification means spreading investments across different assets to reduce risk...",
  "intent": "ASK_CONCEPT",
  "risk": "LOW"
}
```

**Test:** http://127.0.0.1:8000/docs

---

## Risk Levels & Behavior

| Risk | Trigger | Behavior | Example |
|------|---------|----------|---------|
| **LOW** | Concepts, education, facts | Pass through normally | "What is an ETF?" |
| **MED** | Market queries, analysis | Add warning disclaimers | "Should I diversify?" |
| **HIGH** | Direct advice, buy/sell | Blocked by compliance | "Buy TSLA stock!" |

---

## Future Enhancements

- [ ] Wire `app/portfolio_mcp_db.py` into agents (replace mock portfolio server)
- [ ] Scaffold Alembic migrations and run initial migration
- [ ] Redis-backed quote cache with hit/miss metrics
- [ ] OTel tracing + Grafana dashboards
- [ ] Raise test coverage to ≥90% (DeepEval expansion)
- [ ] Docker deployment and canary rollout

---

## Current Status

✅ **Implemented:**
- FastAPI backend on http://localhost:8000
- 9 specialized agents (Educator, Market, Risk Profiler, Portfolio Coach, Strategy, Goal Planning, News Synthesizer, Tax Education, Compliance)
- Multi-provider LLM gateway (OpenAI, Gemini, Anthropic)
- Conversation memory with persistence
- RAG engine (TF-IDF + sentence-transformers)
- SQLAlchemy database layer with portfolio sync
- Streamlit frontend (Chat, Portfolio, Market, About)
- Observability (LangSmith, Arize optional)
- Test suite: 453 passed (all green)
- DeepEval: 12 LLM output quality tests (`tests/deepeval/`)

⚠️ **Pending:**
- Portfolio MCP: agents use mock data; DB-backed variant (`app/portfolio_mcp_db.py`) not yet wired
- Alembic migrations: dependency present, files not yet configured

🚀 **Start locally:**
```powershell
# Backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Frontend (separate terminal)
pip install streamlit
streamlit run frontend/Home.py
```

