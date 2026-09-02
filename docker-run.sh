#!/bin/bash
set -e

# ==============================================================================
# PRAVAH — 1-CLICK DOCKER BUILD & RUN SCRIPT (Bash)
# Builds and runs the unified single container with persistent volume
# ==============================================================================

echo "🐳 Building PRAVAH All-in-One Docker Image..."
docker build -t pravah .

echo "🚀 Launching PRAVAH Single Container on Ports 3000 & 8000..."
docker run --rm -it \
  --name pravah-app \
  -p 3000:3000 \
  -p 8000:8000 \
  -v pravah_data:/app/apps/api \
  pravah
