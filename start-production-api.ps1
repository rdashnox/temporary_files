$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (!(Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

$env:APP_ENV = if ($env:APP_ENV) { $env:APP_ENV } else { "production" }
$env:SEED_DEMO_DATA = if ($env:SEED_DEMO_DATA) { $env:SEED_DEMO_DATA } else { "false" }
$env:AUTO_CREATE_DB = if ($env:AUTO_CREATE_DB) { $env:AUTO_CREATE_DB } else { "false" }
$workers = if ($env:WEB_CONCURRENCY) { $env:WEB_CONCURRENCY } else { "4" }

Write-Host "Starting FinMark API in production-like mode with $workers worker(s)."
& ".\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers $workers --proxy-headers
