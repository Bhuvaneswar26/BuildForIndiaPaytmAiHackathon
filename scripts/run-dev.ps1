# Start all four processes in separate windows (Windows PowerShell)

$root = Split-Path -Parent $PSScriptRoot
if (-not $root) {
    $root = (Get-Location).Path
}

function Start-Svc($title, $dir, $cmd) {

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "
        Set-Location '$dir';

        if (-not (Test-Path '.\.venv\Scripts\python.exe')) {
            if (Test-Path '.venv') {
                Remove-Item -Recurse -Force '.venv'
            }

            python -m venv .venv
        }

        .\.venv\Scripts\python.exe -m pip install --upgrade pip;

        .\.venv\Scripts\python.exe -m pip install -r requirements.txt;

        $cmd
        "
    ) -WindowStyle Normal
}

Start-Svc `
    "GST notify :8091" `
    "$root\02-alert-agent" `
    ".\.venv\Scripts\python.exe -m uvicorn notify_bridge.http_bridge:app --port 8091 --reload"

Start-Sleep -Seconds 2

Start-Svc `
    "GST alerts :8090" `
    "$root\02-alert-agent" `
    ".\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8090 --reload"

Start-Svc `
    "GST advisor :8100" `
    "$root\03-gst-advisor" `
    ".\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8100 --reload"

Start-Sleep -Seconds 2

Start-Svc `
    "GST ingest :8088" `
    "$root\01-ingest-pipeline" `
    "`$env:APP_ENV='development'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8088 --reload"

Write-Host "Merchant UI  http://127.0.0.1:8088"
Write-Host "Alert agent  http://127.0.0.1:8090/health"
Write-Host "Notify log   http://127.0.0.1:8091/tools/recent"
Write-Host "Advisor      http://127.0.0.1:8100"