param(
    [string]$LegacyHostName = "127.0.0.1",
    [int]$LegacyPort = 3306,
    [string]$LegacyDatabase = "finmark_db",
    [string]$LegacyUser = "root",
    [string]$LegacyPassword = "",
    [switch]$PromptForLegacyPassword,
    [switch]$UseFinmarkAppForLegacyRead,
    [switch]$PreserveVerification,
    [switch]$PreserveAdminPassword,
    [switch]$DryRun,
    [switch]$SkipEnvSync,
    [switch]$SkipMysqlProbe
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if ($UseFinmarkAppForLegacyRead) {
    $LegacyUser = "finmark_app"
    if ([string]::IsNullOrWhiteSpace($LegacyPassword)) { $LegacyPassword = "FinmarkApp@2026!" }
}

if ($PromptForLegacyPassword -and [string]::IsNullOrEmpty($LegacyPassword)) {
    $secure = Read-Host "Enter password for legacy MySQL user '$LegacyUser'" -AsSecureString
    $credential = New-Object System.Management.Automation.PSCredential($LegacyUser, $secure)
    $LegacyPassword = $credential.GetNetworkCredential().Password
}

if (-not $SkipEnvSync) {
    & (Join-Path $PSScriptRoot "sync-enterprise-env-app-user.ps1")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if (-not $SkipMysqlProbe) {
    & (Join-Path $PSScriptRoot "diagnose-mysql-connection.ps1") -HostName $LegacyHostName -Port $LegacyPort
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Migration stopped because MySQL is not reachable. Start MySQL first." -ForegroundColor Red
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
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Running enterprise Auth migrations before legacy import..." -ForegroundColor Cyan
& $python -m backend.enterprise.scripts.run_enterprise_migrations --service auth
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$encodedUser = [System.Uri]::EscapeDataString($LegacyUser)
$encodedPassword = [System.Uri]::EscapeDataString($LegacyPassword)
$legacyUrl = "mysql+pymysql://$encodedUser`:$encodedPassword@$LegacyHostName`:$LegacyPort/$LegacyDatabase"

Write-Host "Migrating legacy users, roles, and permissions from '$LegacyDatabase' into finmark_auth_db..." -ForegroundColor Cyan
$argsList = @(
    "-m", "backend.enterprise.scripts.migrate_legacy_auth_to_enterprise",
    "--legacy-url", $legacyUrl
)
if ($PreserveVerification) { $argsList += "--preserve-verification" }
if ($PreserveAdminPassword) { $argsList += "--preserve-admin-password" }
if ($DryRun) { $argsList += "--dry-run" }

& $python @argsList
if ($LASTEXITCODE -ne 0) {
    Write-Host "Legacy Auth migration failed. If you used finmark_app, grant SELECT access on finmark_db first or run this script with root." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "" 
Write-Host "Legacy Auth migration complete." -ForegroundColor Green
Write-Host "Admin can open Admin Dashboard and Product Dashboard." -ForegroundColor Green
Write-Host "Demo admin login: admin@example.com / Admin@12345" -ForegroundColor Cyan
Write-Host "Verify in MySQL Workbench with: verify-auth-migration-workbench.sql" -ForegroundColor Cyan
