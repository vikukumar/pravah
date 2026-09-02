#!/bin/bash
set -e

echo "=========================================================="
echo "🚀 Starting PRAVAH All-in-One Platform..."
echo "=========================================================="

# Create required upload directories
mkdir -p /app/apps/api/uploads/generated

# Trap signals for graceful shutdown
cleanup() {
    echo "Shutting down PRAVAH services gracefully..."
    kill -TERM "$API_PID" "$SCHEDULER_PID" "$WEB_PID" 2>/dev/null || true
    wait "$API_PID" "$SCHEDULER_PID" "$WEB_PID" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Run Database Migrations
echo "🗄️ Running database migrations..."
cd /app/apps/api
/app/venv/bin/alembic upgrade head || /app/venv/bin/python -c "
import asyncio
from app.core.database import Base, engine
from app.models import *
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
"

echo "📦 1. Starting FastAPI Backend Server on port 8000..."
cd /app/apps/api
/app/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "⏰ 2. Starting PRAVAH Background Scheduler..."
/app/venv/bin/python -m app.workers.scheduler &
SCHEDULER_PID=$!

echo "🌐 3. Starting Next.js Web Frontend on port 3000..."
cd /app/apps/web
npm start &
WEB_PID=$!

echo "=========================================================="
echo "✨ PRAVAH is up and running!"
echo "👉 Web Application: http://localhost:3000"
echo "👉 API Documentation: http://localhost:8000/api/v1/docs"
echo "=========================================================="

# Wait on all processes
wait -n "$API_PID" "$SCHEDULER_PID" "$WEB_PID"
