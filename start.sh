#!/bin/bash
# Finnie Chat - Startup Script for macOS/Linux

echo ""
echo "========================================"
echo "  FINNIE CHAT - STARTUP SCRIPT"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -d "venv" ]; then
    echo "ERROR: venv directory not found!"
    echo "Please run this script from the finnie-chat directory"
    exit 1
fi

echo "Starting Finnie Chat..."
echo ""
echo "[1/2] Starting Backend Server (FastAPI)..."
echo "      Port: 8000"
echo "      URL: http://localhost:8000"
echo ""

# Start backend in background
./venv/bin/python -m uvicorn app.main:app --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

echo "[2/2] Starting Frontend (Streamlit)..."
echo "      Port: 8501"
echo "      URL: http://localhost:8501"
echo ""

# Start frontend
./venv/bin/python -m streamlit run frontend/Home.py

# When user stops frontend, also stop backend
kill $BACKEND_PID 2>/dev/null

echo ""
echo "========================================"
echo "  FINNIE CHAT STOPPED"
echo "========================================"
echo ""
