param(
    [switch]$SkipEnvSync,
    [switch]$SkipMysqlProbe,
    [switch]$StartMySQLIfStopped
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Starting local enterprise microservices using the four MySQL databases from .env..." -ForegroundColor Cyan
Write-Host "Make sure you already ran .\setup-enterprise-mysql.ps1 or .\run-enterprise-migrations-mysql.ps1." -ForegroundColor Yellow
Write-Host "Tip: run .\seed-enterprise-mysql.ps1 if you want demo rows visible in MySQL Workbench." -ForegroundColor Yellow

if (-not $SkipEnvSync) {
    & (Join-Path $PSScriptRoot "sync-enterprise-env-app-user.ps1")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
else {
    Write-Host "Skipping .env sync because -SkipEnvSync was provided." -ForegroundColor Yellow
}

if (-not $SkipMysqlProbe) {
    Write-Host "Checking whether MySQL is reachable before starting 12 microservice processes..." -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "diagnose-mysql-connection.ps1") -StartIfStopped:$StartMySQLIfStopped
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Startup stopped because MySQL is not reachable. Start MySQL first, then run this script again." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

& (Join-Path $PSScriptRoot "start-microservices-local.ps1") -UseMySQL
