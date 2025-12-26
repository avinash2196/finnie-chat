# Finnie Chat - PowerShell Debug Startup
# Shows logs directly in console with color coding

Write-Host "`n========================================"
Write-Host "  FINNIE CHAT - DEBUG MODE" -ForegroundColor Cyan
Write-Host "========================================`n"

# Check venv
if (-not (Test-Path "venv")) {
    Write-Host "ERROR: venv directory not found!" -ForegroundColor Red
    Write-Host "Please run from: C:\Users\avina\Codes\finnie-chat"
    pause
    exit 1
}

# Set debug environment
$env:LOG_LEVEL = "DEBUG"

Write-Host "[1/2] Starting Backend Server..." -ForegroundColor Yellow
Write-Host "       Port: 8000"
Write-Host "       Log Level: DEBUG`n"

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; `$env:LOG_LEVEL='DEBUG'; venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --log-level debug" -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host "[2/2] Starting Frontend..." -ForegroundColor Yellow
Write-Host "       Port: 8501`n"

# Start frontend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; venv\Scripts\python.exe -m streamlit run frontend/Home.py" -WindowStyle Normal

Write-Host "`n========================================"
Write-Host "  ✅ STARTUP COMPLETE" -ForegroundColor Green
Write-Host "========================================`n"
Write-Host "Backend logs: Check PowerShell window" -ForegroundColor Cyan
Write-Host "App: http://localhost:8501"
Write-Host "API: http://localhost:8000/docs`n"
