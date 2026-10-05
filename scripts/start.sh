#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-5173}"

if [ "$1" = "--reset" ]; then
    echo "Resetting database and caches..."
    rm -f "$ROOT_DIR/backend/croprisk.db"*
    rm -rf "$ROOT_DIR/backend/.pytest_cache" "$ROOT_DIR/backend/.ruff_cache" "$ROOT_DIR/backend/.coverage" "$ROOT_DIR/frontend/dist"
    find "$ROOT_DIR/backend" -name __pycache__ -type d -not -path "$ROOT_DIR/backend/.venv/*" -exec rm -rf {} + 2>/dev/null || true
    echo "Reset complete."
    exit 0
fi

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
    if command -v uv &>/dev/null; then
        (cd "$ROOT_DIR/backend" && uv sync --extra dev --locked)
    else
        python3 -m venv "$ROOT_DIR/backend/.venv"
        "$ROOT_DIR/backend/.venv/bin/pip" install --upgrade pip
        "$ROOT_DIR/backend/.venv/bin/pip" install -e "$ROOT_DIR/backend[dev]"
    fi
fi

ENV_FILE="$ROOT_DIR/backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating backend/.env from backend/.env.example..."
    cp "$ROOT_DIR/backend/.env.example" "$ENV_FILE"
fi

if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
    echo "Installing frontend dependencies in frontend/..."
    (cd "$ROOT_DIR/frontend" && npm ci)
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

echo "Starting backend (FastAPI) on port $API_PORT..."
(
    cd "$ROOT_DIR/backend"
    source .venv/bin/activate
    exec uvicorn app.main:app --reload --host 127.0.0.1 --port "$API_PORT"
) &
BACKEND_PID=$!

echo "Starting frontend (Vite/React) on port $WEB_PORT..."
(
    cd "$ROOT_DIR/frontend"
    # Run vite directly (not through npm) so the kill in cleanup reaches it.
    exec ./node_modules/.bin/vite --host 127.0.0.1 --port "$WEB_PORT"
) &
FRONTEND_PID=$!

# Wait for the API before printing the URL.
healthy=""
for _ in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:$API_PORT/api/health" >/dev/null; then
        healthy=1
        break
    fi
    sleep 1
done
if [ -z "$healthy" ]; then
    echo "Backend did not start; see the error above."
    exit 1
fi

echo "Open http://localhost:$WEB_PORT (API docs at http://localhost:$API_PORT/docs). Ctrl+C stops both."
wait "$BACKEND_PID" "$FRONTEND_PID"
