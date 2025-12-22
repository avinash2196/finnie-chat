# 🚀 Quick Start Guide - Finnie Chat

## Running the Application

The Finnie Chat system consists of two parts that need to run simultaneously:

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

### Part 2: Frontend (Streamlit Web App)

Open **Terminal 2** and run:

```powershell
cd C:\Users\avina\Codes\finnie-chat
.\venv\Scripts\python.exe -m streamlit run frontend/Home.py
```

You should see:
```
Local URL: http://localhost:8501
Network URL: http://192.168.86.213:8501
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
- Coming in Phase 3 (Weeks 6-8)
- Currently shows placeholder with roadmap

### 📈 Market Tab
- Coming in Phase 4 (Weeks 9-10)
- Currently shows sample market data and screeners

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
- Backend: 6 agents + gateway + 183 tests ✅
- Frontend: Chat tab fully functional ✅
- Integration: Chat → Backend communication ✅
- Placeholder tabs: Portfolio & Market ready for Phase 3 & 4 ✅

### 📅 What's Next (Phase 3 - Weeks 6-8)
- PostgreSQL database setup
- Portfolio management system
- Enhanced portfolio analysis
- Portfolio tracking UI

**See ROADMAP.md for full development plan**
