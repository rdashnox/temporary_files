$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$portHelper = Join-Path $PSScriptRoot "scripts\windows-port-utils.ps1"
if (Test-Path $portHelper) { . $portHelper }

if (!(Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

$env:APP_ENV = if ($env:APP_ENV) { $env:APP_ENV } else { "production" }
$env:SEED_DEMO_DATA = if ($env:SEED_DEMO_DATA) { $env:SEED_DEMO_DATA } else { "false" }
$env:AUTO_CREATE_DB = if ($env:AUTO_CREATE_DB) { $env:AUTO_CREATE_DB } else { "false" }
$workers = if ($env:WEB_CONCURRENCY) { $env:WEB_CONCURRENCY } else { "4" }
$hostAddress = if ($env:FINMARK_API_HOST) { $env:FINMARK_API_HOST } else { "127.0.0.1" }
$preferredPort = if ($env:FINMARK_API_PORT) { [int]$env:FINMARK_API_PORT } else { 8000 }
if (Get-Command Get-FinMarkAvailablePort -ErrorAction SilentlyContinue) {
    $port = Get-FinMarkAvailablePort -PreferredPorts @($preferredPort) -FallbackStart 18000 -Label "production-api"
    Set-FinMarkFrontendApiUrl -ProjectRoot $PSScriptRoot -GatewayPort $port
} else {
    $port = $preferredPort
}

Write-Host ("Starting FinMark API in production-like mode with {0} worker(s) on http://{1}:{2}." -f $workers, $hostAddress, $port)
& ".\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host $hostAddress --port $port --workers $workers --proxy-headers
