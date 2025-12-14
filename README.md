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

# Run market MCP tests only
.\venv\Scripts\python.exe -m pytest tests/test_market.py -v
```

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
