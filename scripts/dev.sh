#!/bin/bash
# Start all Adaptive-OS services for local development.
# Usage: ./scripts/dev.sh

set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "============================================"
echo "  Adaptive-OS — Starting Dev Environment"
echo "============================================"
echo ""

# 1. PostgreSQL (Docker)
echo "[1/5] Starting PostgreSQL..."
docker compose up -d postgres 2>/dev/null || echo "  Warning: Docker not available. Make sure PostgreSQL is running on localhost:5432."
echo ""

# 2. Run database migrations + seed
echo "[2/5] Running migrations & seed..."
cd "$ROOT_DIR/apps/api"
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi
alembic upgrade head 2>/dev/null || echo "  Warning: Migration failed. Is PostgreSQL running?"
python -m aos_api.db.seed 2>/dev/null || echo "  Seed already exists or failed."
cd "$ROOT_DIR"
echo ""

# 3. Build SDK
echo "[3/5] Building SDK..."
npm run build --workspace=@aos/sdk
echo ""

# 4. Start services in background
echo "[4/5] Starting services..."
echo "  - FastAPI API on http://localhost:8000"
echo "  - Demo Store on http://localhost:3000"
echo "  - Dashboard on http://localhost:3001"
echo ""

# FastAPI
cd "$ROOT_DIR/apps/api"
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi
uvicorn aos_api.main:app --reload --port 8000 &
API_PID=$!

# Demo Store
cd "$ROOT_DIR/apps/demo-store"
npx serve . -l 3000 -s &
STORE_PID=$!

# Dashboard
cd "$ROOT_DIR/apps/dashboard"
npm run dev &
DASH_PID=$!

cd "$ROOT_DIR"

echo ""
echo "============================================"
echo "  All services running!"
echo ""
echo "  API:       http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Demo Store: http://localhost:3000"
echo "  Dashboard:  http://localhost:3001"
echo ""
echo "  Demo URLs to test:"
echo "    http://localhost:3000?utm_source=tiktok"
echo "    http://localhost:3000?utm_source=pinterest"
echo "    http://localhost:3000?utm_source=ig"
echo ""
echo "  Press Ctrl+C to stop all services."
echo "============================================"

# Wait and handle cleanup
trap "echo 'Stopping services...'; kill $API_PID $STORE_PID $DASH_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
