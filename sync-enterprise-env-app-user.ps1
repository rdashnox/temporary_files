param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 3306,
    [string]$AppUser = "finmark_app",
    [string]$AppPassword = "FinmarkApp@2026!",
    [int]$RetryCount = 20,
    [int]$RetryDelayMilliseconds = 300
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Read-FinMarkFileWithRetry {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [int]$RetryCount = 20,
        [int]$RetryDelayMilliseconds = 300
    )

    for ($attempt = 1; $attempt -le $RetryCount; $attempt++) {
        try {
            if (!(Test-Path $Path)) { return @() }
            return @([System.IO.File]::ReadAllLines($Path, [System.Text.Encoding]::UTF8))
        }
        catch {
            if ($attempt -eq $RetryCount) { throw }
            Start-Sleep -Milliseconds $RetryDelayMilliseconds
        }
    }
}

function Write-FinMarkFileWithRetry {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][AllowNull()][AllowEmptyCollection()][AllowEmptyString()][string[]]$Lines = @(),
        [int]$RetryCount = 20,
        [int]$RetryDelayMilliseconds = 300
    )

    if ($null -eq $Lines) { $Lines = @() }
    $Lines = @($Lines)

    $parent = Split-Path -Parent $Path
    if ($parent -and !(Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }

    $lastError = $null
    for ($attempt = 1; $attempt -le $RetryCount; $attempt++) {
        $tmpPath = "$Path.tmp.$PID.$attempt"
        try {
            [System.IO.File]::WriteAllLines($tmpPath, $Lines, [System.Text.Encoding]::UTF8)

            if (Test-Path $Path) {
                Remove-Item -LiteralPath $Path -Force -ErrorAction Stop
            }
            Move-Item -LiteralPath $tmpPath -Destination $Path -Force -ErrorAction Stop
            return
        }
        catch {
            $lastError = $_
            try {
                if (Test-Path $tmpPath) { Remove-Item -LiteralPath $tmpPath -Force -ErrorAction SilentlyContinue }
            } catch {}

            if ($attempt -lt $RetryCount) {
                Start-Sleep -Milliseconds $RetryDelayMilliseconds
            }
        }
    }

    Write-Host "" -ForegroundColor Red
    Write-Host "Could not update .env because Windows says the file is being used by another process." -ForegroundColor Red
    Write-Host "Fix options:" -ForegroundColor Yellow
    Write-Host "  1. Close .env in VS Code/Notepad/MySQL Workbench if it is open."
    Write-Host "  2. Stop running backend/microservice processes: .\stop-microservices-local.ps1"
    Write-Host "  3. Close extra PowerShell terminals that are running this project."
    Write-Host "  4. Run this command again: .\sync-enterprise-env-app-user.ps1"
    throw $lastError
}

function Get-FinMarkDotEnvNewLines {
    param(
        # .env may be missing, blank, or temporarily read as no output by PowerShell.
        # Do not make this Mandatory, because Mandatory string parameters reject
        # empty values before the function can rebuild the file.
        [AllowNull()][AllowEmptyCollection()][AllowEmptyString()][string[]]$OriginalLines = @(),
        [Parameter(Mandatory=$true)][System.Collections.IDictionary]$DesiredValues,
        [AllowNull()][AllowEmptyCollection()][AllowEmptyString()][string[]]$RemoveKeys = @()
    )

    if ($null -eq $OriginalLines) { $OriginalLines = @() }
    if ($null -eq $RemoveKeys) { $RemoveKeys = @() }

    $seen = @{}
    $result = New-Object System.Collections.Generic.List[string]

    foreach ($line in @($OriginalLines)) {
        $handled = $false

        foreach ($removeKey in $RemoveKeys) {
            $removePattern = "^\s*#?\s*$([regex]::Escape($removeKey))\s*="
            if ($line -match $removePattern) {
                $handled = $true
                break
            }
        }
        if ($handled) { continue }

        foreach ($key in $DesiredValues.Keys) {
            $pattern = "^\s*#?\s*$([regex]::Escape($key))\s*="
            if ($line -match $pattern) {
                if (-not $seen.ContainsKey($key)) {
                    $result.Add("$key=$($DesiredValues[$key])")
                    $seen[$key] = $true
                }
                $handled = $true
                break
            }
        }

        if (-not $handled) { $result.Add($line) }
    }

    foreach ($key in $DesiredValues.Keys) {
        if (-not $seen.ContainsKey($key)) {
            $result.Add("$key=$($DesiredValues[$key])")
        }
    }

    return @($result.ToArray())
}

$envPath = Join-Path $PSScriptRoot ".env"

if (!(Test-Path $envPath)) {
    if (Test-Path (Join-Path $PSScriptRoot ".env.example")) {
        Copy-Item (Join-Path $PSScriptRoot ".env.example") $envPath -Force
    }
    else {
        New-Item -ItemType File -Force -Path $envPath | Out-Null
    }
}

$encodedUser = [System.Uri]::EscapeDataString($AppUser)
$encodedPassword = [System.Uri]::EscapeDataString($AppPassword)
$baseUrl = "mysql+pymysql://{0}:{1}@{2}:{3}" -f $encodedUser, $encodedPassword, $HostName, $Port

$desired = [ordered]@{
    "ENTERPRISE_MICROSERVICES_ENABLED" = "true"
    "APP_ENV" = "development"
    "AUTO_CREATE_DB" = "false"
    "SEED_DEMO_DATA" = "true"
    "DB_DRIVER" = "mysql+pymysql"
    "DB_HOST" = $HostName
    "DB_PORT" = "$Port"
    "DB_USER" = $AppUser
    "DB_PASSWORD" = $AppPassword
    "DEPLOYMENT_MODE" = "local-enterprise-microservices-mysql"
    "AUTH_DATABASE_URL" = "$baseUrl/finmark_auth_db"
    "ORDER_DATABASE_URL" = "$baseUrl/finmark_order_db"
    "INVENTORY_DATABASE_URL" = "$baseUrl/finmark_inventory_db"
    "NOTIFICATION_DATABASE_URL" = "$baseUrl/finmark_notification_db"
    "EVENT_BUS_ENABLED" = "false"
    "OTEL_ENABLED" = "false"
}

$removeKeys = @("DATABASE_URL")
$rawOriginalLines = Read-FinMarkFileWithRetry -Path $envPath -RetryCount $RetryCount -RetryDelayMilliseconds $RetryDelayMilliseconds
if ($null -eq $rawOriginalLines) {
    $originalLines = @()
}
else {
    $originalLines = @($rawOriginalLines)
}

if ($originalLines.Count -eq 0) {
    Write-Host ".env is missing or blank. Rebuilding enterprise MySQL settings..." -ForegroundColor Yellow
}

$newLines = @(Get-FinMarkDotEnvNewLines -OriginalLines $originalLines -DesiredValues $desired -RemoveKeys $removeKeys)
if ($null -eq $newLines -or $newLines.Count -eq 0) {
    Write-Host "Generated .env content was empty. Rebuilding from required enterprise database values..." -ForegroundColor Yellow
    $newLines = @()
    foreach ($key in $desired.Keys) {
        $newLines += "$key=$($desired[$key])"
    }
}

$oldText = [string]::Join("`n", @($originalLines))
$newText = [string]::Join("`n", @($newLines))

if ($oldText -eq $newText) {
    Write-Host "Enterprise .env is already synchronized for least-privilege MySQL user '$AppUser'. No rewrite needed." -ForegroundColor Green
}
else {
    Write-FinMarkFileWithRetry -Path $envPath -Lines $newLines -RetryCount $RetryCount -RetryDelayMilliseconds $RetryDelayMilliseconds
    Write-Host "Enterprise .env synchronized to use least-privilege MySQL user '$AppUser'." -ForegroundColor Green
}

Write-Host "Database URLs now point to finmark_app, not root." -ForegroundColor Green
Write-Host "Legacy DATABASE_URL removed so the enterprise services use AUTH/ORDER/INVENTORY/NOTIFICATION database URLs." -ForegroundColor Cyan
