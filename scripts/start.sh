#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is not installed or not in PATH."
    exit 1
fi

if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 12))'; then
    echo "Error: CropRisk needs Python 3.12 or newer (found $(python3 --version))."
    exit 1
fi

if ! command -v npm &>/dev/null; then
    echo "Error: npm is not installed or not in PATH."
    exit 1
fi

if [ ! -d "$ROOT_DIR/backend/.venv" ]; then
    echo "Creating Python virtual environment in backend/.venv..."
    python3 -m venv "$ROOT_DIR/backend/.venv"
    echo "Installing backend dependencies..."
    "$ROOT_DIR/backend/.venv/bin/pip" install --upgrade pip
    "$ROOT_DIR/backend/.venv/bin/pip" install -e "$ROOT_DIR/backend[dev]"
fi

ENV_FILE="$ROOT_DIR/backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating backend/.env from backend/.env.example..."
    cp "$ROOT_DIR/backend/.env.example" "$ENV_FILE"
fi

if ! grep -q '^JWT_SECRET=.' "$ENV_FILE"; then
    echo "Generating JWT_SECRET in backend/.env..."
    grep -v '^JWT_SECRET=' "$ENV_FILE" > "$ENV_FILE.tmp" || true
    echo "JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" >> "$ENV_FILE.tmp"
    mv "$ENV_FILE.tmp" "$ENV_FILE"
fi

if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
    echo "Installing frontend dependencies in frontend/..."
    (cd "$ROOT_DIR/frontend" && npm install)
fi

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "Stopping..."
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
}

trap cleanup SIGINT SIGTERM EXIT

echo "Starting backend (FastAPI) on port 8000..."
(
    cd "$ROOT_DIR/backend"
    source .venv/bin/activate
    exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

echo "Starting frontend (Vite/React) on port 5173..."
(
    cd "$ROOT_DIR/frontend"
    exec npm run dev -- --host 127.0.0.1 --port 5173
) &
FRONTEND_PID=$!

echo "Open http://localhost:5173 (API docs at http://localhost:8000/docs). Ctrl+C stops both."
wait "$BACKEND_PID" "$FRONTEND_PID"
