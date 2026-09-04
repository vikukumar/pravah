#!/bin/bash
# ==============================================================================
# PRAVAH — 1-CLICK GRACEFUL RESTART SCRIPT (Bash)
# Gracefully stops running servers and restarts backend and frontend with auto-reload
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔄 [RESTART] Restarting PRAVAH SaaS Platform..."

# 1. Stop existing servers
"$ROOT_DIR/stop.sh"

sleep 1

# 2. Start fresh instances
"$ROOT_DIR/start.sh"
