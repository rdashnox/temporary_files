param(
    [switch]$SkipMysqlProbe,
    [switch]$StartMySQLIfStopped
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "Checking enterprise migration dependencies..." -ForegroundColor Cyan
& $python -c "import alembic, pymysql, sqlalchemy" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing requirements.txt..." -ForegroundColor Yellow
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Synchronizing .env to use the least-privilege finmark_app database user..." -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "sync-enterprise-env-app-user.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not $SkipMysqlProbe) {
    Write-Host "Checking whether MySQL is reachable before running Alembic..." -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "diagnose-mysql-connection.ps1") -StartIfStopped:$StartMySQLIfStopped
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Migration stopped because MySQL is not reachable. Start MySQL first, then run this script again." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "Running enterprise migrations against MySQL URLs from .env..." -ForegroundColor Cyan
& $python -m backend.enterprise.scripts.run_enterprise_migrations
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Migrations completed." -ForegroundColor Green
