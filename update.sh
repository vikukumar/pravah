#!/bin/bash
# ==============================================================================
# PRAVAH — 1-CLICK GRACEFUL UPDATE SCRIPT (Bash)
# Updates dependencies, synchronizes versions, applies migrations, and restarts
# ==============================================================================

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXE="$ROOT_DIR/apps/api/.venv/bin/python"

PULL_GIT=false
NO_RESTART=false

for arg in "$@"; do
    case $arg in
        --pull)
            PULL_GIT=true
            shift
            ;;
        --no-restart)
            NO_RESTART=true
            shift
            ;;
    esac
done

echo "=========================================================="
echo "🔄 [UPDATE] Updating PRAVAH Platform Dependencies & Schemas..."
echo "=========================================================="

# 1. Stop running servers
"$ROOT_DIR/stop.sh"

# 2. Pull Git updates if requested
if [ "$PULL_GIT" = true ]; then
    echo "📥 [1/5] Pulling latest git changes..."
    git pull origin main
else
    echo "ℹ️  [1/5] Skipping git pull (use --pull to fetch from remote)."
fi

# 3. Synchronize versions across all packages
echo "📦 [2/5] Synchronizing repository version descriptors..."
if [ -f "$PYTHON_EXE" ]; then
    "$PYTHON_EXE" "$ROOT_DIR/scripts/version.py" sync
fi

# 4. Update Backend Dependencies
echo "🐍 [3/5] Updating Backend Python dependencies..."
if [ -d "$ROOT_DIR/apps/api/.venv" ]; then
    "$ROOT_DIR/apps/api/.venv/bin/pip" install --upgrade pip
    "$ROOT_DIR/apps/api/.venv/bin/pip" install -r "$ROOT_DIR/apps/api/requirements.txt"
fi

# 5. Update Frontend Dependencies
echo "🌐 [4/5] Updating Frontend Node dependencies..."
cd "$ROOT_DIR/apps/web"
npm install

# 6. Apply Database Migrations
echo "🗄️ [5/5] Applying any pending database schema migrations..."
if [ -f "$PYTHON_EXE" ]; then
    "$PYTHON_EXE" "$ROOT_DIR/scripts/migrate.py"
fi

echo ""
echo "=========================================================="
echo "✓ PRAVAH update completed successfully!"
echo "=========================================================="

# 7. Restart servers unless --no-restart is set
if [ "$NO_RESTART" = false ]; then
    echo "🚀 Launching updated servers..."
    "$ROOT_DIR/start.sh"
else
    echo "Run ./start.sh when ready to launch."
fi
