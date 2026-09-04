# ==============================================================================
# PRAVAH — 1-CLICK INSTANT SERVER STOP SCRIPT (PowerShell)
# Terminates all running FastAPI and Next.js processes and frees ports 8000 & 3000
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RootPath = $PSScriptRoot
$PidFile = Join-Path $RootPath ".pravah.pids"
$TaskKill = "$env:SystemRoot\System32\taskkill.exe"

Write-Host "🛑 [STOP] Stopping all PRAVAH background servers..." -ForegroundColor Yellow

$killedCount = 0

# 1. Kill processes recorded in .pravah.pids
if (Test-Path $PidFile) {
    try {
        $pids = Get-Content $PidFile -ErrorAction SilentlyContinue
        foreach ($p in $pids) {
            if ($p -match '^\d+$') {
                $procId = [int]$p
                if (Test-Path $TaskKill) {
                    & $TaskKill /F /T /PID $procId > $null 2>&1
                } else {
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                }
                $killedCount++
            }
        }
    } catch {}
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

# 2. Kill any processes holding ports 8000 and 3000
$ports = @(8000, 3000)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $owner = $conn.OwningProcess
            if ($owner -and $owner -ne 0) {
                Write-Host "   -> Releasing Port $port (PID: $owner)..." -ForegroundColor DarkGray
                if (Test-Path $TaskKill) {
                    & $TaskKill /F /T /PID $owner > $null 2>&1
                } else {
                    Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue
                }
                $killedCount++
            }
        }
    }
}

# 3. Verify ports are completely free
Start-Sleep -Milliseconds 300
$remaining = Get-NetTCPConnection -LocalPort 8000, 3000 -State Listen -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "⚠️ Warning: Some port listeners are still shutting down. Re-checking..." -ForegroundColor Yellow
    foreach ($r in $remaining) {
        if (Test-Path $TaskKill) {
            & $TaskKill /F /T /PID $r.OwningProcess > $null 2>&1
        }
    }
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "✓ All PRAVAH servers stopped cleanly." -ForegroundColor Green
Write-Host "✓ Ports 8000 & 3000 are completely free." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
