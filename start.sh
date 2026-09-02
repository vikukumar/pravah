#!/bin/bash
set -e

# ==============================================================================
# PRAVAH — 1-CLICK LOCAL STARTUP SCRIPT (Bash)
# Launches both FastAPI Backend and Next.js Frontend concurrently
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "🚀 Launching PRAVAH SaaS Platform Locally..."
echo "=========================================================="

# Trap signals for clean exit
cleanup() {
    echo ""
    echo "🛑 Stopping all PRAVAH servers..."
    kill "$API_PID" "$WEB_PID" 2>/dev/null || true
    wait "$API_PID" "$WEB_PID" 2>/dev/null || true
    echo "✓ All services stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM
cd "$ROOT_DIR/apps/api"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

# 0. Run Database Migrations
echo "🗄️ [0/2] Checking and applying database migrations..."
.venv/bin/python "$ROOT_DIR/scripts/migrate.py"

# 1. Start FastAPI Backend
.venv/bin/uvicorn app.main:app --reload --port 8000 &
API_PID=$!

# 2. Start Next.js Frontend
echo "🌐 [2/2] Starting Next.js Web Frontend on http://localhost:3000..."
cd "$ROOT_DIR/apps/web"
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev &
WEB_PID=$!

echo ""
echo "=========================================================="
echo "✨ PRAVAH is running!"
echo "👉 Web App:  http://localhost:3000"
echo "👉 Setup:    http://localhost:3000/setup"
echo "👉 API Docs: http://localhost:8000/api/v1/docs"
echo "=========================================================="
echo "Press Ctrl+C to stop all servers."

wait
