# ==============================================================================
# PRAVAH — 1-CLICK GRACEFUL UPDATE SCRIPT (PowerShell)
# Updates dependencies, synchronizes versions, applies migrations, and restarts
# ==============================================================================

param(
    [switch]$NoRestart = $false,
    [switch]$PullGit = $false
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RootPath = $PSScriptRoot
$PythonExe = Join-Path $RootPath "apps\api\.venv\Scripts\python.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🔄 [UPDATE] Updating PRAVAH Platform Dependencies & Schemas..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Stop running servers before updating dependencies to avoid file locks
& "$RootPath\stop.ps1"

# 2. Pull Git updates if requested
if ($PullGit) {
    Write-Host "📥 [1/5] Pulling latest git changes..." -ForegroundColor Yellow
    git pull origin main
} else {
    Write-Host "ℹ️  [1/5] Skipping git pull (use -PullGit to pull from remote)." -ForegroundColor DarkGray
}

# 3. Synchronize versions across all packages
Write-Host "📦 [2/5] Synchronizing repository version descriptors..." -ForegroundColor Cyan
if (Test-Path $PythonExe) {
    & $PythonExe "$RootPath\scripts\version.py" sync
}

# 4. Update Backend Python Dependencies
Write-Host "🐍 [3/5] Updating Backend Python dependencies..." -ForegroundColor Cyan
if (Test-Path $PythonExe) {
    & "$RootPath\apps\api\.venv\Scripts\pip.exe" install --upgrade pip
    & "$RootPath\apps\api\.venv\Scripts\pip.exe" install -r "$RootPath\apps\api\requirements.txt"
}

# 5. Update Frontend npm Dependencies
Write-Host "🌐 [4/5] Updating Frontend Node dependencies..." -ForegroundColor Cyan
Push-Location "$RootPath\apps\web"
try {
    npm install
} finally {
    Pop-Location
}

# 6. Apply Database Migrations
Write-Host "🗄️ [5/5] Applying any pending database schema migrations..." -ForegroundColor Cyan
if (Test-Path $PythonExe) {
    & $PythonExe "$RootPath\scripts\migrate.py"
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "✓ PRAVAH update completed successfully!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# 7. Restart servers unless -NoRestart is specified
if (-not $NoRestart) {
    Write-Host "🚀 Launching updated servers..." -ForegroundColor Green
    & "$RootPath\start.ps1"
} else {
    Write-Host "Run .\start.ps1 when ready to launch." -ForegroundColor Yellow
}
