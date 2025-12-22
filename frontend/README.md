# Finnie Chat Frontend

Streamlit-based web interface for the Finnie Chat financial AI assistant.

## Quick Start

### 1. Start the Backend Server

```powershell
cd C:\Users\avina\Codes\finnie-chat
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### 2. Start the Frontend

```powershell
cd C:\Users\avina\Codes\finnie-chat
.\venv\Scripts\streamlit run frontend\Home.py
```

The app will open automatically in your browser at http://localhost:8501

## Features

### 💬 Chat Tab (Home.py)
- **Status:** ✅ Fully Functional
- Real-time chat with Finnie AI
- Conversation history
- User ID tracking
- Backend health monitoring
- Example prompts for quick start

### 📊 Portfolio Tab
- **Status:** 🚧 Backend Complete, Frontend In Progress
- **Backend Features (Ready):** 🆕
  - Database with 5 models (User, Holding, Transaction, Snapshot, SyncLog)
  - Provider pattern (Mock/Robinhood/Fidelity sync)
  - Background scheduler (hourly auto-sync)
  - 10+ REST API endpoints
  - 35 comprehensive tests (all passing)
- **Frontend TODO:**
  - Connect to `/users/{id}/portfolio` endpoint
  - Display real holdings data
  - Show transaction history
  - Visualize asset allocation
  - Add manual sync button

### 📈 Market Tab
- **Status:** 🚧 Placeholder (Phase 4)
- Preview of upcoming market analysis
- Sample market data and screeners
- Will include: real-time data, sector heatmaps, stock screeners

## Usage

### Chat with Finnie

1. Make sure the backend is running on http://localhost:8000
2. Open the Streamlit app
3. Type your question in the chat input
4. Get AI-powered responses instantly

**Example Questions:**
- "What is a dividend?"
- "What's the price of AAPL?"
- "How is my portfolio diversified?"
- "Explain P/E ratio"

### Navigation

Use the sidebar to:
- Switch between tabs (Chat, Portfolio, Market)
- Set your user ID for portfolio tracking
- Check backend connection status
- Clear conversation history

## Development

### Structure

```
frontend/
├── Home.py                      # Main chat interface
└── pages/
    ├── 1_📊_Portfolio.py        # Portfolio tracking (placeholder)
    └── 2_📈_Market.py           # Market analysis (placeholder)
```

### Adding New Features

Streamlit automatically detects new files in the `pages/` directory and adds them to the sidebar navigation.

## Troubleshooting

### Backend Not Connected
- Ensure FastAPI server is running: `.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000`
- Check the backend URL in the app (default: http://localhost:8000)
- Verify the backend health at http://localhost:8000/health

### Streamlit Issues
- Clear cache: Click the hamburger menu → "Clear cache"
- Restart the app: Press `Ctrl+C` in terminal and run again
- Check Streamlit version: `.\venv\Scripts\streamlit --version`

## Next Steps

See [ROADMAP.md](../ROADMAP.md) for upcoming features:
- **Phase 3** (Weeks 6-8): Portfolio system with database
- **Phase 4** (Weeks 9-10): Market trends and screeners
- **Phase 5** (Weeks 11-12): Production deployment
