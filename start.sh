#!/bin/bash
# ==============================================================================
# PRAVAH — 1-CLICK LOCAL STARTUP SCRIPT (Bash)
# Launches FastAPI Backend (Port 8000) and Next.js Frontend (Port 3000)
# Supports Hot-Reload on file changes and Instant Graceful Shutdown on Ctrl+C
# ==============================================================================

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/.pravah.pids"

# Function to cleanly stop any running processes on ports 8000 & 3000
stop_existing_listeners() {
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:8000,3000 2>/dev/null | xargs kill -9 2>/dev/null || true
    elif command -v fuser >/dev/null 2>&1; then
        fuser -k 8000/tcp 3000/tcp 2>/dev/null || true
    fi
}

# Trap signals for immediate, clean exit
cleanup() {
    echo ""
    echo "🛑 [STOP] Stopping all PRAVAH background servers..."
    
    if [ -n "$API_PID" ] && kill -0 "$API_PID" 2>/dev/null; then
        kill "$API_PID" 2>/dev/null || true
    fi
    if [ -n "$WEB_PID" ] && kill -0 "$WEB_PID" 2>/dev/null; then
        kill "$WEB_PID" 2>/dev/null || true
    fi
    
    stop_existing_listeners
    rm -f "$PID_FILE"
    
    echo "✓ [DONE] All services stopped cleanly."
    exit 0
}

trap cleanup SIGINT SIGTERM SIGHUP

# 1. Clean up any previous stale listeners on ports 8000 and 3000
stop_existing_listeners

# 2. Check and setup Python environment
cd "$ROOT_DIR/apps/api"
if [ ! -d ".venv" ]; then
    echo "📦 [SETUP] Creating Python virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# 3. Check and setup Frontend dependencies
cd "$ROOT_DIR/apps/web"
if [ ! -d "node_modules" ]; then
    echo "📦 [SETUP] Installing Frontend Node dependencies..."
    npm install
fi

echo "=========================================================="
echo "🚀 Launching PRAVAH SaaS Platform Locally..."
echo "=========================================================="

# 4. Run Database Migrations
echo "🗄️ [1/3] Checking and applying database migrations..."
"$ROOT_DIR/apps/api/.venv/bin/python" "$ROOT_DIR/scripts/migrate.py"

# 5. Start FastAPI Backend (with Hot-Reload restricted to app/)
echo "🐍 [2/3] Starting FastAPI Backend on http://localhost:8000 (Hot-Reload Enabled)..."
cd "$ROOT_DIR/apps/api"
.venv/bin/uvicorn app.main:app --reload --reload-dir app --port 8000 &
API_PID=$!

# 6. Start Next.js Frontend (with Fast Refresh Hot-Reload)
echo "🌐 [3/3] Starting Next.js Web Frontend on http://localhost:3000 (Hot-Reload Enabled)..."
cd "$ROOT_DIR/apps/web"
npm run dev &
WEB_PID=$!

# Save PIDs
echo "$API_PID" > "$PID_FILE"
echo "$WEB_PID" >> "$PID_FILE"

echo ""
echo "=========================================================="
echo "✨ PRAVAH is running with full auto-reload!"
echo "👉 Web App:  http://localhost:3000"
echo "👉 Setup:    http://localhost:3000/setup"
echo "👉 API Docs: http://localhost:8000/api/v1/docs"
echo "⚡ Backend file changes in apps/api/app will auto-reload."
echo "⚡ Frontend file changes in apps/web will hot-refresh."
echo "=========================================================="
echo "Press Ctrl+C (or run ./stop.sh) to stop all servers instantly."
echo ""

# Wait for background processes
wait "$API_PID" "$WEB_PID"
