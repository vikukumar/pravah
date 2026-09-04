# ==============================================================================
# PRAVAH — 1-CLICK LOCAL STARTUP SCRIPT (PowerShell)
# Launches FastAPI Backend (Port 8000) and Next.js Frontend (Port 3000)
# Supports Hot-Reload on file changes and Instant Graceful Shutdown on Ctrl+C
# ==============================================================================

# Force UTF-8 encoding across PowerShell session and child processes
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
if (Get-Command chcp.com -ErrorAction SilentlyContinue) {
    chcp.com 65001 > $null 2>&1
} elseif (Test-Path "$env:SystemRoot\System32\chcp.com") {
    & "$env:SystemRoot\System32\chcp.com" 65001 > $null 2>&1
}

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$RootPath = $PSScriptRoot
$PythonExe = Join-Path $RootPath "apps\api\.venv\Scripts\python.exe"
$PidFile = Join-Path $RootPath ".pravah.pids"
$TaskKill = "$env:SystemRoot\System32\taskkill.exe"

# Helper function to forcefully kill any process tree and free ports
function Stop-PortListeners {
    param([int[]]$Ports)
    foreach ($p in $Ports) {
        $conns = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
        if ($conns) {
            foreach ($c in $conns) {
                $owner = $c.OwningProcess
                if ($owner -and $owner -ne 0) {
                    if (Test-Path $TaskKill) {
                        & $TaskKill /F /T /PID $owner > $null 2>&1
                    } else {
                        Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue
                    }
                }
            }
        }
    }
}

# 1. Clean up any previous stale processes on ports 8000 & 3000
Stop-PortListeners @(8000, 3000)
if (Test-Path $PidFile) {
    try {
        $oldPids = Get-Content $PidFile -ErrorAction SilentlyContinue
        foreach ($op in $oldPids) {
            if ($op -match '^\d+$') {
                if (Test-Path $TaskKill) {
                    & $TaskKill /F /T /PID [int]$op > $null 2>&1
                } else {
                    Stop-Process -Id [int]$op -Force -ErrorAction SilentlyContinue
                }
            }
        }
    } catch {}
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

# 2. Setup Python environment if missing
if (-not (Test-Path $PythonExe)) {
    Write-Host "[SETUP] Python virtual environment not found. Setting up..." -ForegroundColor Yellow
    & "C:\Program Files\Python312\python.exe" -m venv "$RootPath\apps\api\.venv"
    & "$RootPath\apps\api\.venv\Scripts\pip.exe" install -r "$RootPath\apps\api\requirements.txt"
}

# 3. Setup Node modules if missing
if (-not (Test-Path "$RootPath\apps\web\node_modules")) {
    Write-Host "[SETUP] Installing Next.js frontend dependencies..." -ForegroundColor Yellow
    Push-Location "$RootPath\apps\web"
    npm install
    Pop-Location
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🚀 Launching PRAVAH SaaS Platform Locally..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 4. Run Database Migrations
Write-Host "🗄️ [1/3] Checking and applying database migrations..." -ForegroundColor Cyan
& $PythonExe "$RootPath\scripts\migrate.py"

# 5. Launch FastAPI Backend (with Hot Reload restricted to app/ directory)
Write-Host "🐍 [2/3] Starting FastAPI Backend on http://localhost:8000 (Hot-Reload Enabled)..." -ForegroundColor Green
$apiArgs = "-m uvicorn app.main:app --reload --reload-dir app --port 8000"
$apiProc = Start-Process -FilePath $PythonExe `
    -ArgumentList $apiArgs `
    -WorkingDirectory "$RootPath\apps\api" `
    -NoNewWindow `
    -PassThru

# 6. Launch Next.js Web Frontend (with Fast Refresh Hot Reload)
Write-Host "🌐 [3/3] Starting Next.js Web Frontend on http://localhost:3000 (Hot-Reload Enabled)..." -ForegroundColor Green
$webProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c npm run dev" `
    -WorkingDirectory "$RootPath\apps\web" `
    -NoNewWindow `
    -PassThru

# Save PIDs for stop.ps1 and restart.ps1
"$($apiProc.Id)`n$($webProc.Id)" | Out-File -FilePath $PidFile -Encoding ascii -Force

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "✨ PRAVAH is running with full auto-reload!" -ForegroundColor Green
Write-Host "👉 Web App:  http://localhost:3000" -ForegroundColor White
Write-Host "👉 Setup:    http://localhost:3000/setup" -ForegroundColor White
Write-Host "👉 API Docs: http://localhost:8000/api/v1/docs" -ForegroundColor White
Write-Host "⚡ Backend file changes in apps/api/app will auto-reload." -ForegroundColor DarkGray
Write-Host "⚡ Frontend file changes in apps/web will hot-refresh." -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C (or run .\stop.ps1) to stop all servers instantly." -ForegroundColor Yellow
Write-Host ""

try {
    # Keep active while both child processes are running
    while ((-not $apiProc.HasExited) -and (-not $webProc.HasExited)) {
        Start-Sleep -Milliseconds 500
    }
}
finally {
    Write-Host "`n[STOP] Stopping all PRAVAH background servers..." -ForegroundColor Yellow

    # Forcefully terminate both process trees instantly
    if ($apiProc -and -not $apiProc.HasExited) {
        if (Test-Path $TaskKill) {
            & $TaskKill /F /T /PID $apiProc.Id > $null 2>&1
        } else {
            Stop-Process -Id $apiProc.Id -Force -ErrorAction SilentlyContinue
        }
    }

    if ($webProc -and -not $webProc.HasExited) {
        if (Test-Path $TaskKill) {
            & $TaskKill /F /T /PID $webProc.Id > $null 2>&1
        } else {
            Stop-Process -Id $webProc.Id -Force -ErrorAction SilentlyContinue
        }
    }

    # Ensure ports 8000 and 3000 are completely released
    Stop-PortListeners @(8000, 3000)

    if (Test-Path $PidFile) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    }

    Write-Host "[DONE] All services stopped cleanly." -ForegroundColor Green
}
