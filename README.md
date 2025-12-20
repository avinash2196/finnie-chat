# finnie-chat

Local FastAPI-based LLM orchestration assistant with MCP servers for market data and RAG-based education.

## Architecture

- **LLM Orchestration**: Routes queries by intent (market, education, compliance)
- **MCP Market Server**: Real-time stock quotes via yfinance with caching
- **RAG Engine**: TF-IDF-based retrieval over finance knowledge base
- **Guardrails**: Input validation, output compliance filtering

## Quick Start (PowerShell)

### Setup

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create .env with your OpenAI API key
echo "OPENAI_API_KEY=sk-proj-..." > .env
```

### Run Server

```powershell
# Start FastAPI server (includes MCP market server)
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Server runs on http://127.0.0.1:8000
# Interactive docs available at http://127.0.0.1:8000/docs
```

### Example Requests

```powershell
# Market query
$headers = @{"Content-Type"="application/json"}
$body = @{"message"="What is SPY stock price?"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -Headers $headers -Body $body

# Education query
$body = @{"message"="Explain bond pricing"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -Headers $headers -Body $body
```

### Run Tests

```powershell
# Run all tests
.\venv\Scripts\python.exe -m pytest tests/ -v

# Run memory tests
.\venv\Scripts\python.exe -m pytest tests/test_memory.py -v

# Run market MCP tests only
.\venv\Scripts\python.exe -m pytest tests/test_market.py -v
```

## Conversation Memory

This project includes a **conversation memory system** that maintains chat history and context across turns.

### Features

- **Per-conversation history**: Tracks all messages in a conversation session
- **Message metadata**: Stores intent and risk classification with each message
- **Context-aware responses**: LLM agents use recent conversation history for coherent answers
- **Automatic persistence**: Optionally saves conversations to disk (`chroma/conversations/`)
- **Message pruning**: Keeps only recent messages (default: 100 per conversation) to manage memory
- **Query interface**: Easy retrieval of messages and formatted context for LLM

### Usage Example

```powershell
# First request (creates new conversation)
$body = @{
    "message"="What is a bond?"
} | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -Headers $headers -Body $body
$conversationId = $response.conversation_id

# Follow-up request (uses same conversation for context)
$body = @{
    "message"="How do they work?"
    "conversation_id"=$conversationId
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -Headers $headers -Body $body
```

The orchestrator automatically uses recent conversation history to provide coherent, context-aware responses.

### Memory Storage

- **In-memory**: Conversions are stored in RAM during app runtime
- **File persistence** (optional): Conversations saved to `chroma/conversations/` as JSON files
- **Global singleton**: Single memory instance shared across all requests via `get_memory()`

### Configuration

- Max messages per conversation: 100 (configurable in `app/memory.py`)
- Persist directory: `chroma/conversations/` (loaded on app startup)
- Auto-pruning: Old messages dropped when limit exceeded (keeps most recent)

## MCP Servers

### Market MCP Server (`app/mcp/market_server.py`)

Provides real-time stock data:

- **Tool**: `get_quote(ticker: str)` → Returns price, change%, currency, timestamp
- **Caching**: 30-second TTL per ticker
- **Error Handling**: Graceful fallback on yfinance failures

**Usage**: Automatically invoked by market agent when user asks about stocks.

## Configuration

- `.env` — Contains `OPENAI_API_KEY` (not committed)
- `data/finance_kb.txt` — Knowledge base for RAG retrieval
- `chroma/embeddings.pkl` — Persisted TF-IDF embeddings
- `chroma/conversations/` — Persisted conversation history (JSON files)

## Notes

- Project uses TF-IDF for RAG (lightweight, no native dependencies)
- To upgrade to semantic embeddings: install `torch`, `sentence-transformers`, and VC++ redistributable
- Git repository initialized; ready for remote push

## Project Structure

```
finnie-chat/
├── app/
│   ├── main.py              # FastAPI entrypoint
│   ├── llm.py               # OpenAI client (lazy-loaded)
│   ├── intent.py            # Intent classification
│   ├── guardrails.py        # Input/output validation
│   ├── agents/              # Agent implementations
│   │   ├── orchestrator.py  # Main dispatch logic
│   │   ├── market.py        # Stock market agent (uses MCP)
│   │   ├── educator.py      # Education agent (uses RAG)
│   │   └── compliance.py    # Compliance filtering
│   ├── mcp/                 # MCP servers & clients
│   │   ├── market_server.py # Market data MCP server
│   │   └── market.py        # Market client wrapper
│   └── rag/                 # RAG pipeline
│       ├── store.py         # TF-IDF vector store
│       └── ingest.py        # Knowledge base ingestion
├── data/
│   └── finance_kb.txt       # Finance knowledge base
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   └── test_market.py       # Market MCP tests
├── .env                     # Environment variables (not committed)
├── .gitignore
├── README.md
└── ARCHITECTURE.md          # Detailed architecture docs
```

To push to a remote:

```powershell
git remote add origin <your-repo-url>
git push -u origin main
```

## AI Gateway

This project now includes an AI Gateway that centralizes LLM requests for reliability, cost control, and observability.

- File: `app/gateway.py`
- Features: multi-provider routing (OpenAI, Gemini, Anthropic), request caching, circuit breaker, priority-based failover, metrics
- Docs: see `GATEWAY.md` for detailed configuration and best practices

### Environment variables

Add provider keys to your `.env` to enable providers:

```powershell
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=your-gemini-key
GEMINI_ENDPOINT=https://your-gemini-endpoint.example.com
ANTHROPIC_API_KEY=sk-ant-...
```

### Key endpoints

- `GET /health` — basic health check
- `GET /metrics` — gateway metrics: `total_requests`, `cache_hits`, `cache_hit_rate_percent`, `failures`, `providers_active`

Example metrics call (PowerShell):

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/metrics" -Method GET | ConvertTo-Json -Depth 3
```

### How to call the gateway (programmatic)

All agent LLM calls use the gateway automatically. You can also call it directly:

```python
from app.llm import call_llm, get_gateway_metrics

resp = call_llm(
	system_prompt="You are a helpful assistant.",
	user_prompt="Explain bond pricing",
	temperature=0.2
)

metrics = get_gateway_metrics()
print(metrics)
```

### Best practices

- Provide multiple providers (primary + fallback) via environment variables
- Use caching for repeated prompts (education agent) and short TTLs for fresh data (market agent)
- Monitor `/metrics` and tune circuit breaker thresholds and provider priority based on observed failures and latency

