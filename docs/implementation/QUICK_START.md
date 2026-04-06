# Quick Start Guide — Finnie Chat

> **Platform note:** This guide uses PowerShell syntax (Windows). For macOS/Linux, swap `.\venv\Scripts\Activate.ps1` for `source venv/bin/activate` and `.\` paths for `./`.

## Get the code

```powershell
git clone https://github.com/avinash2196/finnie-chat.git
cd finnie-chat
```

View the repository on GitHub: https://github.com/avinash2196/finnie-chat
Repository docs: https://github.com/avinash2196/finnie-chat/tree/main/docs

## Prerequisites

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
pip install streamlit   # frontend dependency (not in requirements.txt)
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```powershell
# Minimum viable — OpenAI key required
echo "OPENAI_API_KEY=sk-proj-..." > .env

# Optional fallback providers
echo "GEMINI_API_KEY=your-key" >> .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Optional observability (safe no-ops if omitted)
echo "LANGSMITH_API_KEY=lsv2_pt_..." >> .env
echo "LANGSMITH_PROJECT=finnie-chat" >> .env
```

### 4. Initialise the database

```powershell
python -c "from app.database import init_db; init_db()"
```

You should see: `Database initialized successfully!`

## Running the Application

You can use the startup script (recommended) or run backend and frontend separately.

### Option A: Start Both (Recommended)

```powershell
cd finnie-chat
start.bat
```

This opens two terminals:
- Backend (FastAPI) on http://localhost:8000
- Frontend (Streamlit) on http://localhost:8501

### Option B: Backend only (FastAPI Server)

Open **Terminal 1** and run (with venv activated):

```powershell
uvicorn app.main:app --port 8000
```

You should see:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

✅ **Backend is ready** when you see these messages.

### Option C: Frontend only (Streamlit Web App)

Open **Terminal 2** and run (with venv activated):

```powershell
streamlit run frontend/Home.py
```

You should see:
```
Local URL: http://localhost:8501
```

✅ **Frontend is ready** when you see these messages. A browser window will automatically open.

## Accessing the Application

Once both are running, open your browser and go to:
- **Main App:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs

## Using Finnie Chat

### 💬 Chat Tab (Home)
1. Enter your user ID in the sidebar (default: user_001)
2. Type your question in the chat input
3. Get AI-powered responses from Finnie

**Try asking:**
- "What is a dividend?"
- "What's the price of AAPL?"
- "How is my portfolio diversified?"
- "Explain P/E ratio"

### 📊 Portfolio Tab
- Holdings table with metrics and details
- Asset allocation pie chart and concentration summary
- Transaction history with summary (10-year default window)
- Performance & analytics (Sharpe, volatility, 30-day chart)
- Manage tab (add holdings, update prices)

### 📈 Market Trends
- Market overview (indices, gainers/losers, sector heatmap)
- Stock screeners (dividend, growth, value, momentum, high volume)
- Strategy ideas by risk level
- Sector analysis leaders and trends

## Troubleshooting

### Backend Not Running
- **Error:** `Connection refused` on port 8000
- **Solution:** Make sure Terminal 1 command is running and shows "Uvicorn running"

### Frontend Not Running
- **Error:** `Connection refused` on port 8501
- **Solution:** Make sure Terminal 2 command is running and shows "Server started on port 8501"

### Chat Not Working
- **Error:** "Backend Offline" in sidebar
- **Solution:** Check that backend is running (see "Backend Not Running" above)

### Cannot Access http://localhost:8501
- **Solution:** The browser should open automatically. If not:
  1. Open browser manually
  2. Navigate to http://localhost:8501
  3. Check Terminal 2 for errors

## Stopping the Application

To stop either service:
1. Go to the terminal running it
2. Press `Ctrl+C`
3. Type `y` and press Enter if prompted

## System Status

### ✅ What's Complete
- Backend: Orchestrator + 6 agents, gateway, tests ✅
- Database: SQLAlchemy models + sync system ✅
- Providers: Mock/Robinhood/Fidelity ✅
- Background Sync: Hourly auto-sync ✅
- REST API: 18+ endpoints (portfolio, analytics, market, strategy) ✅
- Frontend: Chat, Portfolio, Market Trends ✅

### 📅 Optional Enhancements
- PostgreSQL database (optional)
- Docker + deployment
- Monitoring and auth

**See ROADMAP.md for full development plan**
