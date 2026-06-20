param(
    [switch]$ResetDemo,
    [switch]$NoSampleOrders,
    [switch]$SkipEnvSync,
    [switch]$SkipMysqlProbe,
    [switch]$StartMySQLIfStopped,
    [string]$HostName = "127.0.0.1",
    [int]$Port = 3306,
    [string]$AppUser = "finmark_app",
    [string]$AppPassword = "FinmarkApp@2026!"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not $SkipEnvSync) {
    & (Join-Path $PSScriptRoot "sync-enterprise-env-app-user.ps1") -HostName $HostName -Port $Port -AppUser $AppUser -AppPassword $AppPassword
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if (-not $SkipMysqlProbe) {
    Write-Host "Checking whether MySQL is reachable before migration/seeding..." -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "diagnose-mysql-connection.ps1") -HostName $HostName -Port $Port -StartIfStopped:$StartMySQLIfStopped
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Seeding stopped because MySQL is not reachable. Start MySQL first, then run this script again." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
    Write-Host "Python virtual environment not found. Creating .venv..." -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "Checking backend dependencies..." -ForegroundColor Cyan
& $python -c "import fastapi, sqlalchemy, pymysql, alembic" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing backend dependencies from requirements.txt..." -ForegroundColor Yellow
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Running enterprise MySQL database migrations before seeding..." -ForegroundColor Cyan
& $python -m backend.enterprise.scripts.run_enterprise_migrations
if ($LASTEXITCODE -ne 0) {
    Write-Host "Migration failed. If the message says WinError 10061, start MySQL Server first or run .\diagnose-mysql-connection.ps1." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Seeding four dedicated enterprise MySQL databases..." -ForegroundColor Cyan
$argsList = @("-m", "backend.enterprise.scripts.seed_enterprise_databases")
if ($ResetDemo) { $argsList += "--reset-demo" }
if ($NoSampleOrders) { $argsList += "--no-sample-orders" }
& $python @argsList
if ($LASTEXITCODE -ne 0) {
    Write-Host "Seeding failed. Check the .env database URLs and MySQL Workbench permissions." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "" 
Write-Host "Dedicated database seeding complete." -ForegroundColor Green
Write-Host "Open MySQL Workbench, right-click SCHEMAS, and choose Refresh All." -ForegroundColor Green
Write-Host "Suggested tables to show:" -ForegroundColor Cyan
Write-Host "  finmark_auth_db.auth_users"
Write-Host "  finmark_inventory_db.inventory_products"
Write-Host "  finmark_order_db.order_orders"
Write-Host "  finmark_order_db.order_items"
Write-Host "  finmark_notification_db.notification_messages"
