# Finnie-Chat: Architecture & Data Flow

## System Overview

Finnie-Chat is a sophisticated financial AI system with an Orchestrator plus 6 specialized agents that process user questions through a multi-layered reasoning and synthesis pipeline, combining intent classification, portfolio analysis, market data, and safety guardrails.

**Key Improvement (Dec 2025):** Portfolio MCP server is now fully database-backed. Agents see real user holdings, transactions, and profiles from SQLite/PostgreSQL.

---

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
   ├─ [Risk Profiler Agent] ◄─ Portfolio MCP Server ◄─ DATABASE
   │                            • get_user_holdings(user_id)
   │                            • Queries: User, Holding tables
   │
   ├─ [Portfolio Coach Agent] ◄─ Portfolio MCP Server ◄─ DATABASE
   │                             • get_user_profile(user_id)
   │                             • get_transaction_history()
   │
   ├─ [Strategy Agent] ◄─ Portfolio MCP Server ◄─ DATABASE
   │                       • Analyzes actual holdings
   │                       • Identifies opportunities
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

## Architecture Changes (Dec 2025)

### Before (Mock Data)
```python
# Portfolio MCP used hardcoded data
MOCK_HOLDINGS = {
    "user_123": {  # Only this user had data
        "AAPL": {...},
        "MSFT": {...}
    }
}
```

### After (Database-Backed)
```python
# Portfolio MCP queries real database
def get_user_holdings(user_id):
    user = db.query(User).filter(
        (User.id == user_id) | (User.username == user_id)
    ).first()
    
    holdings = db.query(Holding).filter(
        Holding.user_id == user.id
    ).all()
    
    return format_holdings(holdings)
```

## Complete Request Flowchart

```
User Query
   │
   ▼
┌─────────────────────────────────────────┐
│   Backend API (FastAPI)                 │
│   POST /chat                            │
│   ├─ message: "What stocks do I own?"   │
│   ├─ user_id: "user_002"  ← NEW         │
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
│   ORCHESTRATOR (now receives user_id)   │

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
│ EDUCATOR AGENT   │  │ MARKET AGENT     │  │ STRATEGY/ANALYSIS   │
│ ────────────────│  │ ────────────────│  │ ────────────────────│
│ Module:         │  │ Module:         │  │ (Planned for v2)    │
│ app/agents/     │  │ app/agents/     │  │                     │
│ educator.py     │  │ market.py       │  │ • Diversification   │
│                 │  │                 │  │ • Risk Scoring      │
│ Data Source:    │  │ Data Source:    │  │ • Portfolio Analysis│
│ • RAG Engine    │  │ • yFinance API  │  └─────────────────────┘
│ • TF-IDF        │  │ • MCP Server    │
│   Embeddings    │  │   (future)      │
│ • Finance KB    │  │                 │
│   (ChromaDB)    │  │ Returns:        │
│                 │  │ • Price         │
│ Returns:        │  │ • % Change      │
│ • Explanation   │  │ • Currency      │
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
- TF-IDF Embeddings (scikit-learn)
- ChromaDB persistence (`chroma/embeddings.pkl`)
- Finance Knowledge Base (`data/finance_kb.txt`)

**Example Flow:**
```
User: "What is diversification?"
   ↓
Intent: ASK_CONCEPT (LOW risk)
   ↓
Educator Agent queries RAG
   ↓
Returns: "Diversification means spreading investments across..."
```

### 2. Market Agent
**Purpose:** Fetch live market data and stock prices

**Module:** `app/agents/market.py`

**Data Source:**
- yFinance API (`app/mcp/market.py`)
- Live market prices and metrics
- Daily percentage changes

**Example Flow:**
```
User: "What is the price of AAPL?"
   ↓
Intent: ASK_MARKET (LOW risk)
   ↓
Market Agent extracts ticker: AAPL
   ↓
Calls: get_quote('AAPL')
   ↓
Returns: Price $278.28, +0.09% change
```

### 3. Compliance Agent
**Purpose:** Deterministic safety filtering based on risk level

**Module:** `app/agents/compliance.py`

**Rules:**
- **LOW risk:** Pass through unchanged
- **MED risk:** Add warning disclaimers
- **HIGH risk:** Block/reject response

**Example Flow:**
```
User: "Should I buy Tesla stock?"
   ↓
Intent: ADVICE (HIGH risk)
   ↓
LLM generates response
   ↓
Output Guardrails block HIGH risk
   ↓
Compliance Agent returns:
"I can't provide investment advice, but I can explain..."
```

---

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

## Data Sources & External Integrations

### 1. LLM: OpenAI GPT-4o-mini
- **Environment Variable:** `OPENAI_API_KEY` (loaded from `.env`)
- **Usage:** Reasoning + Synthesis layers
- **Model:** `gpt-4o-mini` (cost-efficient)

### 2. Market Data: yFinance
- **Python Package:** `yfinance`
- **Data:** Stock prices, % change, currency
- **No auth required** (public API)

### 3. Knowledge Base: Local ChromaDB
- **Storage:** `chroma/embeddings.pkl`
- **Content:** `data/finance_kb.txt`
- **Embedding Method:** TF-IDF (scikit-learn)
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

## Future Enhancements (v2+)

- [ ] Portfolio Agent (analyze user holdings)
- [ ] Strategy Agent (screening & ideas)
- [ ] Risk Profiler Agent
- [ ] MCP Server integration (advanced analytics)
- [ ] Persistent user sessions
- [ ] Conversation memory/context
- [ ] Multi-turn dialog support
- [ ] Backend database (PostgreSQL for user data)

---

## Current Status

✅ **Completed:**
- FastAPI server running on http://127.0.0.1:8000
- Input/output guardrails
- Intent classification
- Educator Agent (RAG with TF-IDF)
- Market Agent (yFinance)
- Compliance filtering
- Environment variable loading from `.env`
- OpenAI API integration (lazy-loaded)

🚀 **Ready to Test:**
```powershell
# Terminal 1: Start server
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Terminal 2: Visit browser
# http://127.0.0.1:8000/docs
```

Try asking:
- "What is portfolio diversification?"
- "What is the price of AAPL today?"
- "Should I buy Tesla?" (will be blocked as HIGH risk)

