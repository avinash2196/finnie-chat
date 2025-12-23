# 🚀 Quick Start Guide - Finnie Chat

## Get the code

```powershell
git clone https://github.com/avinash2196/finnie-chat.git
cd finnie-chat
```

## Prerequisites

Before running the application, ensure the database is initialized:

```powershell
cd C:\Users\avina\Codes\finnie-chat
.\venv\Scripts\python.exe -c "from app.database import init_db; init_db()"
```

You should see: `Database initialized successfully!`

## Running the Application

You can use the startup script (recommended) or run backend and frontend separately.

### Option A: Start Both (Recommended)

```powershell
cd C:\Users\avina\Codes\finnie-chat
start.bat
```

This opens two terminals:
- Backend (FastAPI) on http://localhost:8000
- Frontend (Streamlit) on http://localhost:8501

### Part 1: Backend (FastAPI Server)

Open **Terminal 1** and run:

```powershell
cd C:\Users\avina\Codes\finnie-chat
.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

You should see:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

✅ **Backend is ready** when you see these messages.

### Option B: Frontend (Streamlit Web App)

Open **Terminal 2** and run:

```powershell
cd C:\Users\avina\Codes\finnie-chat
.\venv\Scripts\python.exe -m streamlit run frontend/Home.py
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
