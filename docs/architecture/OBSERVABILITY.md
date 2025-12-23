# Observability & Monitoring Guide

## Overview

Finnie Chat includes comprehensive observability with **Arize AI** and **LangSmith** for production monitoring, debugging, and LLM tracing.

## Features

### ✅ What's Tracked

| Category | Metrics | Tools |
|----------|---------|-------|
| **LLM Runs** | Hierarchical traces (intent → router → agents → composer) | LangSmith |
| **Chat Interactions** | User sessions, intents, risk levels | App-level tracking |
| **Agent Execution** | Individual agent latency, success/failure | App-level tracking |
| **Quality Signals** | Groundedness, relevance, hallucination risk, confidence | Arize AI |
| **Safety Signals** | PII detected, restricted advice, refusal reason | Arize AI |
| **Tags** | prediction_type, model/prompt/agent version, asset/compliance | Arize AI |

---

## Quick Links

- **[Quick Setup](../implementation/OBSERVABILITY_SETUP.md)** — 5-minute setup guide

---

## Setup Instructions

### 1. Arize AI (Prediction Logging, Quality & Safety)

#### Get Arize API Keys
Collect the following from your Arize workspace:
- `ARIZE_API_KEY`
- `ARIZE_SPACE_KEY`
- `ARIZE_ORG_KEY` (optional)

#### Configure Environment Variables
Add to `.env`:
```bash
ARIZE_API_KEY=your-arize-api-key
ARIZE_SPACE_KEY=your-arize-space-key
ARIZE_ORG_KEY=optional-org-key
ARIZE_MODEL_ID=finnie-chat
ARIZE_MODEL_VERSION=1.0.0

# Optional tagging/versioning
PROMPT_VERSION=v1
AGENT_VERSION=1.0.0
```

#### What You'll See in Arize
- Prediction events with rich tags and metadata
- Quality signals (groundedness_score, retrieval_relevance, hallucination_risk, confidence_level)
- Safety signals (pii_detected, restricted_advice_triggered, refusal_reason)

---

### 2. LangSmith (LLM Tracing)

#### Get LangSmith API Key
1. Go to [LangSmith](https://smith.langchain.com)
2. Create account / sign in
3. Go to Settings → API Keys
4. Create new API key

#### Configure Environment Variables
Add to `.env`:
```bash
LANGSMITH_API_KEY=lsv2_pt_abc123...
LANGSMITH_PROJECT=finnie-chat
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

#### What You'll See in LangSmith
- **Traces:** Complete LLM call chains (orchestrator → agents → LLM)
- **Latency:** Per-agent and total response times
- **Token Usage:** Input/output tokens per call
- **Costs:** Estimated costs by provider (OpenAI, Gemini, Claude)
- **Debugging:** Exact prompts sent, responses received
- **Chain Visualization:** Multi-agent orchestration flow

---

## Installation

### Install Observability Packages
```bash
cd C:\Users\avina\Codes\finnie-chat
.\venv\Scripts\activate
pip install -r requirements.txt
```

Packages used:
- `langsmith`
- `arize`

---

## Usage

### Automatic Tracing & Logging
Observability is integrated on app startup:

```python
# app/main.py (already configured)
from app.observability import observability
observability.instrument_fastapi(app)  # optional
```

### Manual Event Tracking
Track custom events in your code:

```python
from app.observability import observability

# Track custom event
observability.track_event("user_signup", {
    "user_id": "user_123",
    "source": "frontend"
})

# Track metric
observability.track_metric("portfolio_value", 50000.0, {
    "user_id": "user_123"
})

# Track exception
try:
    risky_operation()
except Exception as e:
    observability.track_exception(e, {"context": "portfolio_sync"})
```

### Agent Execution Tracking
Use decorators to track agent performance:

```python
from app.observability import track_agent_execution

@track_agent_execution("MarketAgent")
def run_market_agent(message):
    # Your agent code
    return result
```

**Tracks:**
- Execution time
- Success/failure status
- Error details (if failed)

### LLM Call Tracking
Track LLM provider calls:

```python
from app.observability import track_llm_call

@track_llm_call("openai")
def call_openai_api(prompt):
    # API call
    return response
```

**Tracks:**
- Provider name
- Latency
- Success/failure

---

## Monitoring Dashboard

### Check Observability Status
Visit the API endpoint:
```bash
GET http://localhost:8000/observability/status
```

**Response (example):**
```json
{
    "status": {
        "langsmith_available": true,
        "langsmith_enabled": true,
        "langsmith_project": "finnie-chat",
        "opentelemetry_available": false,
        "arize_enabled": true
    },
    "message": "Observability services configured"
}
```

### Health Check with Observability
```bash
GET http://localhost:8000/health
```

**Response:**
```json
{
    "status": "ok",
    "observability": {
        "langsmith_enabled": true,
        "langsmith_project": "finnie-chat",
        "arize_enabled": true
    }
}
```

---

## Tracked Events

### Chat Interactions
**Event:** `chat_interaction`

**Properties:**
- `user_id`: User identifier
- `conversation_id`: Conversation UUID
- `intent`: Classified intent (ASK_CONCEPT, ASK_MARKET, etc.)
- `risk`: Risk level (LOW, MED, HIGH)
- `duration_ms`: Response time in milliseconds
- `verify_sources`: Whether RAG verification was requested

**Metric:** `chat_response_time` (milliseconds)

---

### Agent Executions
**Event:** `{AgentName}_execution`

**Properties:**
- `agent`: Agent name (MarketAgent, EducatorAgent, etc.)
- `duration_ms`: Execution time
- `status`: success or error
- `error`: Error message (if failed)

**Metric:** `{AgentName}_duration` (milliseconds)

---

### LLM API Calls
**Event:** `llm_call`

**Properties:**
- `provider`: openai, gemini, or anthropic
- `duration_ms`: API call latency
- `status`: success or error
- `error`: Error message (if failed)

**Metric:** `llm_{provider}_duration` (milliseconds)

---

### Guardrail Blocks
**Event:** `chat_guardrail_blocked`

**Properties:**
- `user_id`: User who triggered block
- `conversation_id`: Conversation UUID

---

## Arize & LangSmith Dashboards
Use Arize to review logged predictions and quality/safety signals; use LangSmith to inspect hierarchical traces for each chat request.

---

## LangSmith Dashboards

### View Traces
1. Go to [LangSmith Projects](https://smith.langchain.com/projects)
2. Select `finnie-chat` project
3. View individual traces with full chain execution

### Filter by Agent
Use filters:
- `tags.agent: MarketAgent`
- `tags.agent: EducatorAgent`
- etc.

### Performance Analysis
- **Latency P50/P95/P99:** Identify slow agents
- **Token Usage:** Track costs per agent
- **Error Rate:** Spot failing LLM calls

---

## Troubleshooting

### LangSmith Not Tracking
**Check:**
1. ✅ `LANGSMITH_API_KEY` set
2. ✅ `LANGCHAIN_TRACING_V2=true`
3. ✅ Package installed: `pip install langsmith`
4. ✅ Check logs: `observability.get_status()`

### No Data Appearing
**Wait:** Observability data can take 1-5 minutes to appear in Arize/LangSmith dashboards.

### Local Development
For local testing, observability is **optional**:
- Works without Arize/LangSmith configured
- Logs warnings but doesn't fail
- All tracking is no-op if not configured

---

## Production Recommendations

### LangSmith
- ✅ Enable for **production** and **staging** environments
- ✅ Use different projects per environment
- ✅ Set **cost alerts** if token usage spikes
- ✅ Export traces for compliance/auditing

### Cost Management
| Tool | Note |
|------|------|
| **LangSmith** | Pricing based on traces; set project-level limits as needed |
| **Arize** | Pricing based on events/volume; consult Arize account for limits |

---

## Architecture

### Data Flow
```
User Request
    ↓
FastAPI Endpoint
    ↓
Orchestrator (LangSmith tracing)
    ↓
Agents (Custom event tracking)
    ↓
LLM Calls (LangSmith tracing + Arize logging)
    ↓
Database (OpenTelemetry SQLAlchemy)
    ↓
Response (Custom metrics)
```

### Components
- **LangSmith:** LLM run tracing via environment variables
- **Arize:** Prediction logging with tags and quality/safety signals

---

## References

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [Arize Docs](https://docs.arize.com/)

---

## Support

**Issues?**
- Check `app/observability.py` for implementation details
- Run `GET /observability/status` to verify configuration
- Review startup logs for initialization messages
- Test with: `pytest tests/test_observability.py -v`
