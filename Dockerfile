# ==============================================================================
# PRAVAH — ALL-IN-ONE SINGLE CONTAINER DOCKERFILE
# Runs FastAPI Backend (Port 8000) + Next.js Frontend (Port 3000) + Scheduler
# ==============================================================================

# Stage 1: Build Next.js Web Frontend
FROM node:20-alpine AS web-builder

WORKDIR /app

COPY packages/shared-types ./packages/shared-types
COPY apps/web/package*.json ./apps/web/

WORKDIR /app/apps/web
RUN npm ci

COPY apps/web ./
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN npm run build

# Stage 2: Final Single Container (Python 3.12 + Node.js 20 Runtime)
FROM python:3.12-slim-bookworm AS runner

WORKDIR /app

# Install system dependencies, Node.js 20 LTS, curl & dos2unix
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    build-essential \
    dos2unix \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# 1. Install Python Backend Dependencies
COPY apps/api/requirements.txt /app/apps/api/
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r /app/apps/api/requirements.txt

# 2. Copy FastAPI Backend Source
COPY apps/api /app/apps/api

# 3. Copy Built Next.js Frontend
COPY --from=web-builder /app/packages/shared-types /app/packages/shared-types
COPY --from=web-builder /app/apps/web/public /app/apps/web/public
COPY --from=web-builder /app/apps/web/.next /app/apps/web/.next
COPY --from=web-builder /app/apps/web/node_modules /app/apps/web/node_modules
COPY --from=web-builder /app/apps/web/package.json /app/apps/web/package.json

# 4. Copy Startup Entrypoint Script
COPY infrastructure/docker/entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Environment Defaults
ENV ENVIRONMENT=production
ENV PORT=3000
ENV NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
ENV DATABASE_URL=sqlite+aiosqlite:////app/apps/api/pravah.db
ENV DATABASE_SYNC_URL=sqlite:////app/apps/api/pravah.db
ENV SECRET_KEY=pravah_production_single_container_secret_key_32_chars
ENV ENCRYPTION_KEY=pravah_fernet_production_encryption_key_32_bytes

# Expose Web Frontend (3000) and Backend API (8000)
EXPOSE 3000 8000

ENTRYPOINT ["/app/entrypoint.sh"]
