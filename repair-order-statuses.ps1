param(
    [switch]$SkipMysqlProbe,
    [switch]$StartMySQLIfStopped
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not $SkipMysqlProbe) {
    & (Join-Path $PSScriptRoot "diagnose-mysql-connection.ps1") -StartIfStopped:$StartMySQLIfStopped
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
    Write-Host "Missing .venv. Run .\install-enterprise-deps.ps1 first." -ForegroundColor Red
    exit 1
}

& $python -m backend.enterprise.scripts.repair_order_statuses
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "" 
Write-Host "Order status repair complete. Restart microservices and frontend." -ForegroundColor Green
