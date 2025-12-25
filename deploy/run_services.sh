#!/usr/bin/env bash
set -euo pipefail

# Wrapper to start backend (uvicorn) and frontend (streamlit)
# Intended for manual copy to VM and `chmod +x`.

cd /home/ubuntu/finnie-chat
if [ ! -f venv/bin/activate ]; then
  echo "virtualenv not found; please create venv and install requirements"
  exit 1
fi

source ./venv/bin/activate

# log locations
BACKEND_LOG=/var/log/finnie-backend.log
FRONTEND_LOG=/var/log/finnie-frontend.log

touch "$BACKEND_LOG" "$FRONTEND_LOG"
chown $(whoami) "$BACKEND_LOG" "$FRONTEND_LOG" || true

# Start backend
nohup ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 >>"$BACKEND_LOG" 2>&1 &
echo $! > /var/run/finnie-backend.pid

# Start frontend
nohup ./venv/bin/streamlit run frontend/Home.py --server.address 0.0.0.0 --server.port 8501 >>"$FRONTEND_LOG" 2>&1 &
echo $! > /var/run/finnie-frontend.pid

echo "Started backend (pid $(cat /var/run/finnie-backend.pid)) and frontend (pid $(cat /var/run/finnie-frontend.pid))"

wait
