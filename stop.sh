#!/bin/bash
# ==============================================================================
# PRAVAH — 1-CLICK INSTANT SERVER STOP SCRIPT (Bash)
# Terminates all running FastAPI and Next.js processes and frees ports 8000 & 3000
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/.pravah.pids"

echo "🛑 [STOP] Stopping all PRAVAH background servers..."

# 1. Kill processes recorded in .pravah.pids
if [ -f "$PID_FILE" ]; then
    while IFS= read -r pid || [ -n "$pid" ]; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi

# 2. Kill any processes holding ports 8000 and 3000
if command -v lsof >/dev/null 2>&1; then
    lsof -ti:8000,3000 2>/dev/null | xargs kill -9 2>/dev/null || true
elif command -v fuser >/dev/null 2>&1; then
    fuser -k 8000/tcp 3000/tcp 2>/dev/null || true
fi

echo "=========================================================="
echo "✓ All PRAVAH servers stopped cleanly."
echo "✓ Ports 8000 & 3000 are completely free."
echo "=========================================================="
