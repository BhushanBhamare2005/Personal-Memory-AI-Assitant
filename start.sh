#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "Personal AI Memory Assistant"
echo "============================"

if [[ -x ".venv/bin/python" ]]; then
    venv_dir=".venv"
elif [[ -x "venv/bin/python" ]]; then
    venv_dir="venv"
else
    python3 -m venv .venv
    venv_dir=".venv"
fi

source "$venv_dir/bin/activate"
python -m pip install -r requirements.txt

if [[ ! -f ".env" ]]; then
    cp .env.example .env
    echo "Created .env from .env.example."
fi

mkdir -p data/documents logs

echo "Starting backend and frontend. Press Ctrl+C to stop both."
uvicorn src.backend.main:app --reload &
backend_pid=$!
python -m streamlit run src/frontend/app.py &
frontend_pid=$!

stop_services() {
    kill "$backend_pid" "$frontend_pid" 2>/dev/null || true
}
trap stop_services EXIT INT TERM
wait "$backend_pid" "$frontend_pid"
