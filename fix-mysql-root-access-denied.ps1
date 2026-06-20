param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 3306,
    [string]$AppUser = "finmark_app",
    [string]$AppPassword = "FinmarkApp@2026!",
    [switch]$StartAfterFix
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot


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
        if (Test-Path (Join-Path $PSScriptRoot ".env.example")) {
            Copy-Item (Join-Path $PSScriptRoot ".env.example") $Path
        } else {
            New-Item -ItemType File -Force -Path $Path | Out-Null
        }
    }

    $lines = @(Get-Content $Path -ErrorAction SilentlyContinue)
    $pattern = "^\s*#?\s*$([regex]::Escape($Key))\s*="
    $replacement = "$Key=$Value"
    $found = $false
    $newLines = foreach ($line in $lines) {
        if ($line -match $pattern) {
            $found = $true
            $replacement
        } else {
            $line
        }
    }
    if (-not $found) { $newLines += $replacement }
    Set-Content -Path $Path -Value $newLines -Encoding UTF8
}

Write-Host "Fixing MySQL root access-denied configuration for enterprise 4-DB mode..." -ForegroundColor Cyan
$envPath = Join-Path $PSScriptRoot ".env"
$encodedUser = [System.Uri]::EscapeDataString($AppUser)
$encodedPassword = [System.Uri]::EscapeDataString($AppPassword)
$baseUrl = "mysql+pymysql://{0}:{1}@{2}:{3}" -f $encodedUser, $encodedPassword, $HostName, $Port

Set-FinMarkDotEnvValue -Path $envPath -Key "ENTERPRISE_MICROSERVICES_ENABLED" -Value "true"
Set-FinMarkDotEnvValue -Path $envPath -Key "DEPLOYMENT_MODE" -Value "local-enterprise-microservices-mysql"
Set-FinMarkDotEnvValue -Path $envPath -Key "AUTO_CREATE_DB" -Value "false"
Set-FinMarkDotEnvValue -Path $envPath -Key "SEED_DEMO_DATA" -Value "false"
Set-FinMarkDotEnvValue -Path $envPath -Key "EVENT_BUS_ENABLED" -Value "false"
Set-FinMarkDotEnvValue -Path $envPath -Key "OTEL_ENABLED" -Value "false"
Set-FinMarkDotEnvValue -Path $envPath -Key "DB_DRIVER" -Value "mysql+pymysql"
Set-FinMarkDotEnvValue -Path $envPath -Key "DB_HOST" -Value $HostName
Set-FinMarkDotEnvValue -Path $envPath -Key "DB_PORT" -Value "$Port"
Set-FinMarkDotEnvValue -Path $envPath -Key "DB_USER" -Value $AppUser
Set-FinMarkDotEnvValue -Path $envPath -Key "DB_PASSWORD" -Value $AppPassword
Remove-FinMarkDotEnvValue -Path $envPath -Key "DATABASE_URL"
Set-FinMarkDotEnvValue -Path $envPath -Key "AUTH_DATABASE_URL" -Value "$baseUrl/finmark_auth_db"
Set-FinMarkDotEnvValue -Path $envPath -Key "ORDER_DATABASE_URL" -Value "$baseUrl/finmark_order_db"
Set-FinMarkDotEnvValue -Path $envPath -Key "INVENTORY_DATABASE_URL" -Value "$baseUrl/finmark_inventory_db"
Set-FinMarkDotEnvValue -Path $envPath -Key "NOTIFICATION_DATABASE_URL" -Value "$baseUrl/finmark_notification_db"

Write-Host "Updated .env to use the finmark_app account for the four dedicated enterprise databases." -ForegroundColor Green
Write-Host "Important: start-backend.ps1 is for the legacy single backend. Use start-microservices-local-mysql.ps1 for the 4-DB enterprise setup." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next commands:" -ForegroundColor Cyan
Write-Host "  .\verify-enterprise-mysql-databases.ps1"
Write-Host "  .\start-microservices-local-mysql.ps1"
Write-Host ""
Write-Host "If verification fails, run .\setup-enterprise-mysql.ps1 again with your real MySQL root/admin password." -ForegroundColor Yellow

if ($StartAfterFix) {
    & (Join-Path $PSScriptRoot "start-microservices-local-mysql.ps1")
    exit $LASTEXITCODE
}
