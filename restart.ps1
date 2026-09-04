# ==============================================================================
# PRAVAH — 1-CLICK GRACEFUL RESTART SCRIPT (PowerShell)
# Gracefully stops running servers and restarts backend and frontend with auto-reload
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RootPath = $PSScriptRoot

Write-Host "🔄 [RESTART] Restarting PRAVAH SaaS Platform..." -ForegroundColor Cyan

# 1. Stop existing servers cleanly
& "$RootPath\stop.ps1"

Write-Host "`n⏳ Waiting for port release..." -ForegroundColor DarkGray
Start-Sleep -Seconds 1

# 2. Launch start script
Write-Host "🚀 Launching fresh instances..." -ForegroundColor Green
& "$RootPath\start.ps1"
