param(
    [switch]$Legacy
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Import-FinMarkDotEnvFile {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (!(Test-Path $Path)) { return }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { return }
        $key = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

Import-FinMarkDotEnvFile -Path (Join-Path $PSScriptRoot ".env")

$enterpriseEnabled = [System.Environment]::GetEnvironmentVariable("ENTERPRISE_MICROSERVICES_ENABLED", "Process")
$authUrl = [System.Environment]::GetEnvironmentVariable("AUTH_DATABASE_URL", "Process")
$orderUrl = [System.Environment]::GetEnvironmentVariable("ORDER_DATABASE_URL", "Process")
$inventoryUrl = [System.Environment]::GetEnvironmentVariable("INVENTORY_DATABASE_URL", "Process")
$notificationUrl = [System.Environment]::GetEnvironmentVariable("NOTIFICATION_DATABASE_URL", "Process")

if (-not $Legacy -and $enterpriseEnabled -and $enterpriseEnabled.ToLower() -eq "true" -and $authUrl -and $orderUrl -and $inventoryUrl -and $notificationUrl) {
    Write-Host "This project is configured for the FULL ENTERPRISE 4-database microservice mode." -ForegroundColor Cyan
    Write-Host "start-backend.ps1 starts the older single FastAPI app and may use DB_USER/root settings." -ForegroundColor Yellow
    Write-Host "Redirecting to the correct enterprise MySQL microservice launcher..." -ForegroundColor Green
    Write-Host "Use .\start-backend.ps1 -Legacy only if you intentionally want the legacy single-app backend." -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot "start-microservices-local-mysql.ps1")
    exit $LASTEXITCODE
}

$portHelper = Join-Path $PSScriptRoot "scripts\windows-port-utils.ps1"
if (Test-Path $portHelper) { . $portHelper }

if (!(Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

$preferredPort = if ($env:FINMARK_API_PORT) { [int]$env:FINMARK_API_PORT } else { 8000 }
if (Get-Command Get-FinMarkAvailablePort -ErrorAction SilentlyContinue) {
    $port = Get-FinMarkAvailablePort -PreferredPorts @($preferredPort) -FallbackStart 18000 -Label "backend-api"
    Set-FinMarkFrontendApiUrl -ProjectRoot $PSScriptRoot -GatewayPort $port
} else {
    $port = $preferredPort
}

Write-Host ("Starting legacy single-app backend on http://127.0.0.1:{0}" -f $port) -ForegroundColor Green
Write-Host "For the 4 dedicated enterprise databases, use: .\start-microservices-local-mysql.ps1" -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port $port
