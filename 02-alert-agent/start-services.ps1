$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (-not (Test-Path ".venv")) {
    Write-Host "Virtual environment not found. Creating one..."
    python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

Write-Host "Installing Python dependencies..."
python -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..."
    Copy-Item .env.example .env
}

Write-Host "Starting MCP notification bridge on port 8091..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir'; .\.venv\Scripts\Activate.ps1; python -m uvicorn notify_bridge.http_bridge:app --host 0.0.0.0 --port 8091 --reload"

Write-Host "Starting alert agent API on port 8090..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir'; .\.venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload"

Write-Host "Both services are starting in separate terminals."
Write-Host "HTTP Bridge: http://127.0.0.1:8091/health"
Write-Host "Alert Agent: http://127.0.0.1:8090/health"
