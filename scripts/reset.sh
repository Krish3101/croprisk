#!/usr/bin/env bash
set -e

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Stop ./scripts/start.sh first (Ctrl+C). The tables are recreated on the next start.
rm -f backend/croprisk.db backend/croprisk.db-shm backend/croprisk.db-wal
rm -rf backend/.pytest_cache backend/.ruff_cache backend/.coverage backend/htmlcov frontend/dist
find backend -name __pycache__ -type d -not -path 'backend/.venv/*' -exec rm -rf {} +
echo "Database and caches removed. .env, .venv and node_modules were kept."
