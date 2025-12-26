@echo off
REM Finnie Chat - Startup Script with DEBUG logging

echo.
echo ========================================
echo   FINNIE CHAT - DEBUG MODE
echo ========================================
echo.

if not exist "venv\" (
    echo ERROR: venv directory not found!
    pause
    exit /b 1
)

echo Starting Finnie Chat with DEBUG logging...
echo.

REM Set DEBUG log level
set LOG_LEVEL=DEBUG

echo [1/2] Starting Backend Server (FastAPI) with DEBUG logs...
echo       Port: 8000
echo       URL: http://localhost:8000
echo       Log Level: DEBUG
echo.

REM Start backend in a new window with DEBUG
start "Finnie Backend [DEBUG]" cmd /k "cd /d %cd% && set LOG_LEVEL=DEBUG && venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --log-level debug"

REM Wait for backend to start
timeout /t 3 /nobreak

echo [2/2] Starting Frontend (Streamlit)...
echo       Port: 8501
echo       URL: http://localhost:8501
echo.

REM Start frontend
start "Finnie Frontend" cmd /k "cd /d %cd% && venv\Scripts\python.exe -m streamlit run frontend/Home.py"

echo.
echo ========================================
echo   ✅ DEBUG MODE ACTIVE
echo ========================================
echo.
echo Backend logs in: "Finnie Backend [DEBUG]" window
echo Access app at: http://localhost:8501
echo API Docs at: http://localhost:8000/docs
echo.
pause
