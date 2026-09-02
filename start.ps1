# ==============================================================================
# PRAVAH — 1-CLICK LOCAL STARTUP SCRIPT (PowerShell)
# Launches both FastAPI Backend and Next.js Frontend concurrently
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

if (-not (Test-Path $PythonExe)) {
    Write-Host "[SETUP] Python virtual environment not found. Setting up..." -ForegroundColor Yellow
    & "C:\Program Files\Python312\python.exe" -m venv "$RootPath\apps\api\.venv"
    & "$RootPath\apps\api\.venv\Scripts\pip.exe" install -r "$RootPath\apps\api\requirements.txt"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[PRAVAH] Launching SaaS Platform Locally..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 0. Run Database Migrations
Write-Host "[0/2] Checking and applying database migrations..." -ForegroundColor Cyan
& $PythonExe "$RootPath\scripts\migrate.py"

# 1. Start FastAPI Backend in background job
Write-Host "[1/2] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
$BackendJob = Start-Job -ScriptBlock {
    param($root)
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONUTF8 = "1"
    Set-Location "$root\apps\api"
    & "$root\apps\api\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
} -ArgumentList $RootPath

# 2. Start Next.js Frontend in background job
Write-Host "[2/2] Starting Next.js Web Frontend on http://localhost:3000..." -ForegroundColor Green
$FrontendJob = Start-Job -ScriptBlock {
    param($root)
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    Set-Location "$root\apps\web"
    npm run dev
} -ArgumentList $RootPath

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "[READY] PRAVAH is running!" -ForegroundColor Green
Write-Host "  * Web App:  http://localhost:3000" -ForegroundColor White
Write-Host "  * Setup:    http://localhost:3000/setup" -ForegroundColor White
Write-Host "  * API Docs: http://localhost:8000/api/v1/docs" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop all servers." -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        # Receive job output
        $bOut = Receive-Job -Job $BackendJob
        if ($bOut) { Write-Host ($bOut -join "`n") -ForegroundColor DarkGray }

        $fOut = Receive-Job -Job $FrontendJob
        if ($fOut) { Write-Host ($fOut -join "`n") -ForegroundColor Gray }

        Start-Sleep -Milliseconds 500
    }
}
finally {
    Write-Host "`n[STOP] Stopping all PRAVAH background servers..." -ForegroundColor Yellow
    Stop-Job $BackendJob, $FrontendJob -ErrorAction SilentlyContinue
    Remove-Job $BackendJob, $FrontendJob -ErrorAction SilentlyContinue
    Write-Host "[DONE] All services stopped." -ForegroundColor Green
}
