param(
    [string]$AdminUser = "root",
    [string]$AdminPassword = "",
    [string]$HostName = "127.0.0.1",
    [int]$Port = 3306,
    [string]$AppUser = "finmark_app",
    [string]$AppPassword = "FinmarkApp@2026!",
    [switch]$SkipMigrations,
    [switch]$SkipSeed,
    [switch]$StartMySQLIfStopped
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. (Join-Path $PSScriptRoot "scripts\mysql-connection-utils.ps1")

function Find-FinMarkMySqlCli {
    $cmd = Get-Command mysql -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $possible = @(
        "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe",
        "C:\Program Files\MySQL\MySQL Server 8.3\bin\mysql.exe",
        "C:\Program Files\MySQL\MySQL Server 8.2\bin\mysql.exe",
        "C:\Program Files\MySQL\MySQL Server 8.1\bin\mysql.exe",
        "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
        "C:\xampp\mysql\bin\mysql.exe",
        "C:\laragon\bin\mysql\mysql-8.0\bin\mysql.exe"
    )
    foreach ($path in $possible) {
        if (Test-Path $path) { return $path }
    }
    return $null
}

function ConvertFrom-SecureStringToPlainText {
    param([System.Security.SecureString]$SecureString)
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureString)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}


function Remove-FinMarkDotEnvValue {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Key
    )

    if (!(Test-Path $Path)) { return }

    $lines = @(Get-Content $Path -ErrorAction SilentlyContinue)
    $pattern = "^\s*#?\s*$([regex]::Escape($Key))\s*="
    $newLines = foreach ($line in $lines) {
        if ($line -notmatch $pattern) { $line }
    }
    Set-Content -Path $Path -Value $newLines -Encoding UTF8
}

function Set-FinMarkDotEnvValue {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Key,
        [Parameter(Mandatory=$true)][AllowEmptyString()][string]$Value
    )

    if (!(Test-Path $Path)) {
        New-Item -ItemType File -Force -Path $Path | Out-Null
    }

    $lines = @(Get-Content $Path -ErrorAction SilentlyContinue)
    $pattern = "^\s*#?\s*$([regex]::Escape($Key))\s*="
    $replacement = "$Key=$Value"
    $found = $false
    $newLines = foreach ($line in $lines) {
        if ($line -match $pattern) {
            $found = $true
            $replacement
        }
        else {
            $line
        }
    }
    if (-not $found) {
        $newLines += $replacement
    }
    Set-Content -Path $Path -Value $newLines -Encoding UTF8
}

Write-Host "FinMark Enterprise MySQL setup" -ForegroundColor Cyan
Write-Host "This will create four dedicated databases and one least-privilege app user." -ForegroundColor Yellow
Write-Host ""

Write-Host "Checking MySQL server TCP connection before setup..." -ForegroundColor Cyan
$mysqlReady = Test-FinMarkTcpPort -HostName $HostName -Port $Port
if (-not $mysqlReady -and $StartMySQLIfStopped) {
    Start-FinMarkPossibleMySqlServices
    Start-Sleep -Seconds 3
    $mysqlReady = Test-FinMarkTcpPort -HostName $HostName -Port $Port
}
if (-not $mysqlReady) {
    Show-FinMarkMySqlConnectionGuidance -HostName $HostName -Port $Port
    Write-Host "Setup stopped before running mysql.exe because MySQL is not reachable." -ForegroundColor Red
    exit 1
}

$mysql = Find-FinMarkMySqlCli
if (-not $mysql) {
    Write-Host "MySQL CLI mysql.exe was not found." -ForegroundColor Red
    Write-Host "Option A: Install MySQL Server and make sure mysql.exe is in PATH." -ForegroundColor Yellow
    Write-Host "Option B: Open setup-4-dedicated-databases-workbench.sql in MySQL Workbench and execute it manually." -ForegroundColor Yellow
    exit 1
}

if (-not $AdminPassword) {
    $securePassword = Read-Host "Enter MySQL admin password for '$AdminUser' on $($HostName):$Port. Press Enter if blank" -AsSecureString
    $AdminPassword = ConvertFrom-SecureStringToPlainText $securePassword
}

$templatePath = Join-Path $PSScriptRoot "setup-4-dedicated-databases.sql"
if (!(Test-Path $templatePath)) {
    Write-Host "Missing setup-4-dedicated-databases.sql. Please re-extract the project ZIP." -ForegroundColor Red
    exit 1
}

$tempSql = Join-Path $env:TEMP "finmark_setup_4_dedicated_databases.sql"
$sql = Get-Content $templatePath -Raw
$sql = $sql.Replace("__FINMARK_APP_USER__", $AppUser.Replace("'", "''"))
$sql = $sql.Replace("__FINMARK_APP_PASSWORD__", $AppPassword.Replace("'", "''"))
Set-Content -Path $tempSql -Value $sql -Encoding UTF8

Write-Host "Creating databases in MySQL..." -ForegroundColor Cyan
$mysqlArgs = @("--host=$HostName", "--port=$Port", "--user=$AdminUser", "--default-character-set=utf8mb4", "--protocol=tcp")
if ($AdminPassword.Length -gt 0) {
    $mysqlArgs += "--password=$AdminPassword"
}
else {
    $mysqlArgs += "--password="
}
Get-Content $tempSql -Raw | & $mysql @mysqlArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "MySQL database creation failed. Confirm your root/admin password and MySQL service status." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Updating .env for the four dedicated MySQL databases..." -ForegroundColor Cyan
$envPath = Join-Path $PSScriptRoot ".env"
if (!(Test-Path $envPath) -and (Test-Path (Join-Path $PSScriptRoot ".env.example"))) {
    Copy-Item (Join-Path $PSScriptRoot ".env.example") $envPath
}

$encodedUser = [System.Uri]::EscapeDataString($AppUser)
$encodedPassword = [System.Uri]::EscapeDataString($AppPassword)
$baseUrl = "mysql+pymysql://{0}:{1}@{2}:{3}" -f $encodedUser, $encodedPassword, $HostName, $Port

Set-FinMarkDotEnvValue -Path $envPath -Key "ENTERPRISE_MICROSERVICES_ENABLED" -Value "true"
Set-FinMarkDotEnvValue -Path $envPath -Key "APP_ENV" -Value "development"
Set-FinMarkDotEnvValue -Path $envPath -Key "AUTO_CREATE_DB" -Value "false"
Set-FinMarkDotEnvValue -Path $envPath -Key "SEED_DEMO_DATA" -Value "true"
Set-FinMarkDotEnvValue -Path $envPath -Key "DB_DRIVER" -Value "mysql+pymysql"
Set-FinMarkDotEnvValue -Path $envPath -Key "DB_HOST" -Value $HostName
Set-FinMarkDotEnvValue -Path $envPath -Key "DB_PORT" -Value "$Port"
# Keep the legacy single-app DB_* values away from root so accidental legacy starts do not fail with root access denied.
# Full enterprise mode still uses the four AUTH/ORDER/INVENTORY/NOTIFICATION database URLs below.
Set-FinMarkDotEnvValue -Path $envPath -Key "DB_USER" -Value $AppUser
Set-FinMarkDotEnvValue -Path $envPath -Key "DB_PASSWORD" -Value $AppPassword
Remove-FinMarkDotEnvValue -Path $envPath -Key "DATABASE_URL"
Set-FinMarkDotEnvValue -Path $envPath -Key "DEPLOYMENT_MODE" -Value "local-enterprise-microservices-mysql"
Set-FinMarkDotEnvValue -Path $envPath -Key "AUTH_DATABASE_URL" -Value "$baseUrl/finmark_auth_db"
Set-FinMarkDotEnvValue -Path $envPath -Key "ORDER_DATABASE_URL" -Value "$baseUrl/finmark_order_db"
Set-FinMarkDotEnvValue -Path $envPath -Key "INVENTORY_DATABASE_URL" -Value "$baseUrl/finmark_inventory_db"
Set-FinMarkDotEnvValue -Path $envPath -Key "NOTIFICATION_DATABASE_URL" -Value "$baseUrl/finmark_notification_db"
Set-FinMarkDotEnvValue -Path $envPath -Key "EVENT_BUS_ENABLED" -Value "false"
Set-FinMarkDotEnvValue -Path $envPath -Key "OTEL_ENABLED" -Value "false"

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "Installing/checking backend dependencies..." -ForegroundColor Cyan
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Dependency installation failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

if (-not $SkipMigrations) {
    Write-Host "Running Alembic migrations for Auth, Order, Inventory, and Notification databases..." -ForegroundColor Cyan
    & $python -m backend.enterprise.scripts.run_enterprise_migrations
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Alembic migrations failed. Check the database URL values in .env." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

if (-not $SkipSeed) {
    Write-Host "Seeding demo admin, sample inventory, and notification data..." -ForegroundColor Cyan
    & $python -m backend.enterprise.scripts.seed_enterprise_databases
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Database seed failed. The databases were created, but demo data was not inserted." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Enterprise MySQL setup complete." -ForegroundColor Green
Write-Host "Open MySQL Workbench, right-click SCHEMAS, and choose Refresh All." -ForegroundColor Green
Write-Host "You should see:" -ForegroundColor Green
Write-Host "  finmark_auth_db" -ForegroundColor White
Write-Host "  finmark_order_db" -ForegroundColor White
Write-Host "  finmark_inventory_db" -ForegroundColor White
Write-Host "  finmark_notification_db" -ForegroundColor White
Write-Host ""
Write-Host "Verify with:" -ForegroundColor Cyan
Write-Host "  .\verify-enterprise-mysql-databases.ps1"
Write-Host ""
Write-Host "Start local microservices using MySQL with:" -ForegroundColor Cyan
Write-Host "  .\start-microservices-local-mysql.ps1"
