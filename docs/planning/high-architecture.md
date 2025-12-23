# High-Level System Architecture

## Complete System Overview

The Finnie Financial AI system is a multi-tab AI assistant that integrates specialized agents, real-time market data, portfolio analytics, and educational content to provide personalized financial guidance.

---

## Complete Architecture Diagram

```mermaid
flowchart TB
    %% =========================
    %% User Interface Layer
    %% =========================
    subgraph UI["🖥️ Finnie Multi-Tab User Interface"]
        CHAT["💬 Chat Tab<br/>(Ask Questions)"]
        PORT["📊 Portfolio Tab<br/>(Holdings & Risk)"]
        MARKET["📈 Market Tab<br/>(Trends & Ideas)"]
    end

    UI -->|all requests| API["🔌 Backend API Layer<br/>━━━━━━━━━━━━━<br/>Sessions • Auth<br/>Rate Limiting • Routing"]

    %% =========================
    %% Intelligence Layer
    %% =========================
    subgraph CORE["🧠 AI Orchestration Layer"]
        ORCH["LLM Orchestrator<br/>━━━━━━━━━━━━━<br/>• Intent Router<br/>• Tool Dispatcher<br/>• Response Fusion<br/>• Safety Control"]
        MEM["💾 Memory Store<br/>━━━━━━━━━━━━━<br/>• User Profile<br/>• Risk Level<br/>• Query History<br/>• Tab Context"]
    end

    API --> ORCH
    ORCH <--->|read/write| MEM

    %% =========================
    %% Agent Layer
    %% =========================
    subgraph AGENTS["🤖 Domain Agents (LLM Tools)"]
        direction LR
        EDU["📚 Educator<br/>Concepts &<br/>Explanations"]
        PORTC["📊 Portfolio Coach<br/>Holdings &<br/>Risk Analysis"]
        MKTAN["📈 Market Analyst<br/>Trends & Data"]
        RISK["⚠️ Risk Profiler<br/>Risk Scoring &<br/>Assessment"]
        STRAT["🎯 Strategy &<br/>Screening<br/>Ideas & Screens"]
        COMP["🛡️ Compliance &<br/>Safety<br/>Advice Filter"]
    end

    ORCH -->|dispatches| AGENTS
    AGENTS -->|returns results| ORCH

    %% =========================
    %% Data & Tooling Layer
    %% =========================
    subgraph DATA["📚 Data & Tooling Layer"]
        RAG["🔍 RAG Engine<br/>━━━━━━━━━━━━<br/>Vector DB<br/>Knowledge Base<br/>Document Search"]
        MCP["🔧 MCP Server<br/>━━━━━━━━━━━━<br/>Portfolio Analytics<br/>Risk Models<br/>Screeners"]
        MKTAPI["📊 Market APIs<br/>━━━━━━━━━━━━<br/>yFinance<br/>Alpha Vantage<br/>News APIs"]
        PDB["💾 Portfolio DB<br/>━━━━━━━━━━━━<br/>User Holdings<br/>Transactions<br/>Cache"]
    end

    %% Agent connections to data layer
    EDU --> RAG
    PORTC --> PDB
    PORTC --> MKTAPI
    PORTC --> MCP
    MKTAN --> MKTAPI
    MKTAN --> MCP
    RISK --> MCP
    RISK --> PDB
    STRAT --> RAG
    STRAT --> MCP

    %% Response back to API
    ORCH --> API
    API --> UI

    %% Color styling
    style UI fill:#E3F2FD,stroke:#1976D2,stroke-width:3px
    style CHAT fill:#BBDEFB,stroke:#1565C0
    style PORT fill:#E1BEE7,stroke:#6A1B9A
    style MARKET fill:#B2DFDB,stroke:#004D40
    
    style API fill:#C8E6C9,stroke:#388E3C,stroke-width:2px
    
    style CORE fill:#FFF9C4,stroke:#F57F17,stroke-width:3px
    style ORCH fill:#FFE0B2,stroke:#F57C00,stroke-width:2px,color:#000
    style MEM fill:#4ECDC4,stroke:#1A8A80,stroke-width:2px,color:#fff
    
    style AGENTS fill:#F0F4C3,stroke:#9E9D24,stroke-width:2px
    style EDU fill:#A8E6CF,stroke:#56B49F
    style PORTC fill:#FFD3B6,stroke:#FFAA47,color:#000
    style MKTAN fill:#FFAAA5,stroke:#FF8877,color:#fff
    style RISK fill:#FF8B94,stroke:#FF5A6E,color:#fff
    style STRAT fill:#95B8D1,stroke:#547AA5,color:#000
    style COMP fill:#EAC4D5,stroke:#D47BA0,color:#000
    
    style DATA fill:#FCE4EC,stroke:#E91E63,stroke-width:2px
    style RAG fill:#F8BBD0,stroke:#C2185B,color:#000
    style MCP fill:#FCCDE7,stroke:#AD1457,color:#000
    style MKTAPI fill:#F8BBD0,stroke:#C2185B,color:#000
    style PDB fill:#B2DFDB,stroke:#00796B,color:#000
```

---

## System Layers Explained

### Layer 1: User Interface
Three specialized tabs for different user needs:

| Tab | Purpose | Features |
|-----|---------|----------|
| **Chat** | General Q&A about finance | Ask anything, get explanations, market context |
| **Portfolio** | Personal investment analysis | View holdings, risk metrics, diversification |
| **Market** | Explore market opportunities | Trends, screeners, sector analysis, ideas |

### Layer 2: Backend API
- Session management & authentication
- Request routing to orchestrator
- Response formatting & aggregation
- Rate limiting & caching

### Layer 3: AI Orchestration
**Orchestrator** - LLM-based decision maker:
- Analyzes user intent
- Routes to appropriate agents
- Manages multi-agent conversations
- Fuses responses from multiple agents
- Enforces safety & compliance

**Memory Store** - Context persistence:
- User profile (risk level, goals, knowledge)
- Conversation history
- Tab-specific context
- Previous queries & results

### Layer 4: Domain Agents (6 Specialized Tools)

Each agent is a specialized LLM tool:

| Agent | Specialization | Uses |
|-------|----------------|------|
| **Educator** | Financial education | RAG, Knowledge Base |
| **Portfolio Coach** | Portfolio analysis | Portfolio DB, Market APIs, MCP |
| **Market Analyst** | Market trends | Market APIs, MCP |
| **Risk Profiler** | Risk assessment | MCP, Portfolio DB |
| **Strategy & Screening** | Investment ideas | MCP, RAG |
| **Compliance** | Safety filtering | Safety rules, guardrails |

### Layer 5: Data & Tooling
External systems providing data & analytics:

| Tool | Purpose | Data |
|------|---------|------|
| **RAG Engine** | Knowledge retrieval | Financial docs, guides, FAQs |
| **MCP Server** | Analytics & metrics | Risk models, screeners, analysis |
| **Market APIs** | Real-time prices & news | Stock data, indices, news |
| **Portfolio DB** | User holdings storage | Assets, transactions, history |

---

## Complete Data Flow Examples

### Example 1: Chat Question about Diversification

```mermaid
sequenceDiagram
    User->>Chat: "How diversified is my portfolio?"
    Chat->>API: Send question + user_id
    API->>Orch: Route to orchestrator
    Orch->>MEM: Load user profile & portfolio context
    Orch->>Coach: Analyze holdings
    Coach->>PDB: Fetch user holdings
    Coach->>MCP: Calculate diversification metrics
    MCP-->>Coach: Diversification score
    Coach->>Orch: "Portfolio is 60% tech - need diversification"
    Orch->>Educator: Explain diversification concept
    Educator->>RAG: Search diversification docs
    RAG-->>Educator: Concept explanation
    Educator->>Orch: "Diversification means..."
    Orch->>Comp: Validate response (no bad advice)
    Comp-->>Orch: Response approved
    Orch->>API: Formatted response
    API->>Chat: Display answer
    Chat-->>User: Show analysis + explanation
```

### Example 2: Market Tab - Stock Screener

```mermaid
sequenceDiagram
    User->>Market: Run screener: "Dividend stocks"
    Market->>API: Screener request
    API->>Orch: Route to strategy agent
    Orch->>MEM: Load user preferences
    Orch->>Strategy: Run dividend screener
    Strategy->>MCP: Execute screen query
    MCP->>MKTAPI: Get dividend data
    MKTAPI-->>MCP: List of dividend stocks
    MCP-->>Strategy: 50 matching stocks
    Strategy->>RAG: Get explanations
    RAG-->>Strategy: "Why dividend stocks" docs
    Strategy->>Orch: Results + explanations
    Orch->>Comp: Verify no bad recommendations
    Orch->>API: Format results
    API->>Market: Display screener results
    Market-->>User: Show list with details
```

### Example 3: Portfolio Tab - Risk Assessment

```mermaid
sequenceDiagram
    User->>Portfolio: View portfolio analysis
    Portfolio->>API: Request analysis
    API->>Orch: Route portfolio query
    Orch->>RiskProfile: Assess risk
    RiskProfile->>PDB: Get holdings
    RiskProfile->>MCP: Calculate risk metrics
    MCP-->>RiskProfile: Risk score, volatility
    RiskProfile->>Coach: Analyze holdings
    Coach->>MKTAPI: Get current prices
    Coach->>MCP: Calculate allocation
    Coach->>Orch: Holdings analysis
    Orch->>Educator: Explain portfolio concepts
    Orch->>Comp: Safety check
    Orch->>API: Aggregate results
    API->>Portfolio: Send metrics + charts
    Portfolio-->>User: Display dashboard
```

---

## Key Features by Tab

### Chat Tab ✨
- Real-time conversational AI
- Educational content from RAG
- Market context integration
- Personalized by user risk profile

### Portfolio Tab 📊
- Real-time holdings valuation
- Risk metrics & analytics
- Diversification analysis
- Sector breakdown visualization

### Market Tab 📈
- Live market indices
- Sector performance heatmap
- Custom stock screeners
- Investment strategy ideas

---

## Technical Highlights

✅ **Multi-Agent Architecture** - Specialized agents for different domains
✅ **Memory & Context** - Maintains user state across sessions
✅ **RAG Integration** - Knowledge-based document search
✅ **MCP Server** - Advanced analytics & modeling
✅ **Real-time Data** - Live market APIs integration
✅ **Safety First** - Compliance agent filters all advice
✅ **Modular Design** - Easy to add new agents/data sources

