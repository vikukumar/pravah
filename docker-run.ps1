# ==============================================================================
# PRAVAH — 1-CLICK DOCKER BUILD & RUN SCRIPT (PowerShell)
# Builds and runs the unified single container with persistent volume
# ==============================================================================

Write-Host "🐳 Building PRAVAH All-in-One Docker Image..." -ForegroundColor Cyan
docker build -t pravah .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "🚀 Launching PRAVAH Single Container on Ports 3000 & 8000..." -ForegroundColor Green
docker run --rm -it `
  --name pravah-app `
  -p 3000:3000 `
  -p 8000:8000 `
  -v pravah_data:/app/apps/api `
  pravah
