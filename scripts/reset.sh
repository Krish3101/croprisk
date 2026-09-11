#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "CropRisk Environment Reset"

echo "Checking for running services..."
for PORT in 8000 5173; do
    PIDS=$(lsof -ti :$PORT 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo "Found process running on port $PORT (PID: $PIDS). Terminating..."
        kill -9 $PIDS 2>/dev/null || true
    fi
done

echo "Removing database files..."
rm -f "$ROOT_DIR/backend/croprisk.db" \
      "$ROOT_DIR/backend/croprisk.db-shm" \
      "$ROOT_DIR/backend/croprisk.db-wal" \
      "$ROOT_DIR/croprisk.db" \
      "$ROOT_DIR/croprisk.db-shm" \
      "$ROOT_DIR/croprisk.db-wal"

echo "Cleaning Python caches and test artifacts..."
find "$ROOT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$ROOT_DIR" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find "$ROOT_DIR" -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
rm -f "$ROOT_DIR/backend/.coverage" "$ROOT_DIR/.coverage"
rm -rf "$ROOT_DIR/backend/htmlcov"

echo "Cleaning frontend build output..."
rm -rf "$ROOT_DIR/frontend/dist"

if [ ! -f "$ROOT_DIR/backend/.env" ]; then
    echo "Restoring backend/.env from backend/.env.example..."
    cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
fi

if [ -f "$ROOT_DIR/backend/.venv/bin/python" ]; then
    echo "Initializing clean database schema..."
    (
        cd "$ROOT_DIR/backend"
        "$ROOT_DIR/backend/.venv/bin/python" -c"
from app.db import Base, engine
from app.domain.crops import validate_catalogue
validate_catalogue()
Base.metadata.create_all(bind=engine)
print('   Database tables created successfully.')
"
    )
else
    echo "Virtual environment not found; schema will be automatically created upon first './scripts/start.sh'."
fi

echo ""
echo "CropRisk reset complete!"
echo "• Database wiped and reinitialized"
echo "• Temporary caches and build artifacts cleared"
echo "• Ready for a clean start with ./scripts/start.sh"
