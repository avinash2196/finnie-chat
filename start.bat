@echo off
REM Finnie Chat - Startup Script for Windows
REM This script starts both the backend and frontend

echo.
echo ========================================
echo   FINNIE CHAT - STARTUP SCRIPT
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "venv\" (
    echo ERROR: venv directory not found!
    echo Please run this script from: C:\Users\avina\Codes\finnie-chat
    pause
    exit /b 1
)

echo Starting Finnie Chat...
echo.
echo [1/2] Starting Backend Server (FastAPI)...
echo       Port: 8000
echo       URL: http://localhost:8000
echo.

REM Start backend in a new window
start "Finnie Backend" cmd /k "cd /d %cd% && venv\Scripts\python.exe -m uvicorn app.main:app --port 8000"

REM Wait a few seconds for backend to start
timeout /t 3 /nobreak

echo [2/2] Starting Frontend (Streamlit)...
echo       Port: 8501
echo       URL: http://localhost:8501
echo.

REM Start frontend in a new window
start "Finnie Frontend" cmd /k "cd /d %cd% && venv\Scripts\python.exe -m streamlit run frontend/Home.py"

echo.
echo ========================================
echo   ✅ STARTUP COMPLETE
echo ========================================
echo.
echo Access the app at: http://localhost:8501
echo API Docs at: http://localhost:8000/docs
echo.
echo Press CTRL+C in either window to stop
echo.
pause
