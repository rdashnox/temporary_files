# Run from the project root in PowerShell.
# This starts the legacy single-app FastAPI backend unless enterprise mode is enabled.

param(
  [switch]$Legacy
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

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

Import-FinMarkDotEnvFile -Path (Join-Path $projectRoot ".env")
$enterpriseEnabled = [System.Environment]::GetEnvironmentVariable("ENTERPRISE_MICROSERVICES_ENABLED", "Process")
$hasEnterpriseUrls = [System.Environment]::GetEnvironmentVariable("AUTH_DATABASE_URL", "Process") -and `
  [System.Environment]::GetEnvironmentVariable("ORDER_DATABASE_URL", "Process") -and `
  [System.Environment]::GetEnvironmentVariable("INVENTORY_DATABASE_URL", "Process") -and `
  [System.Environment]::GetEnvironmentVariable("NOTIFICATION_DATABASE_URL", "Process")

if (-not $Legacy -and $enterpriseEnabled -and $enterpriseEnabled.ToLower() -eq "true" -and $hasEnterpriseUrls) {
  Write-Host "Enterprise 4-database mode detected. Starting the microservice launcher instead of the legacy backend." -ForegroundColor Cyan
  & (Join-Path $projectRoot "start-microservices-local-mysql.ps1")
  exit $LASTEXITCODE
}

$portHelper = Join-Path $projectRoot "scripts\windows-port-utils.ps1"
if (Test-Path $portHelper) { . $portHelper }

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
  . .\.venv\Scripts\Activate.ps1
}

python -m backend.scripts.check_database_connection
if ($LASTEXITCODE -ne 0) {
  Write-Host "Database connection failed. Check your .env DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, and DB_NAME." -ForegroundColor Red
  Write-Host "If you are using the 4 dedicated enterprise DBs, run .\start-microservices-local-mysql.ps1 instead." -ForegroundColor Yellow
  exit $LASTEXITCODE
}

$preferredPort = if ($env:FINMARK_API_PORT) { [int]$env:FINMARK_API_PORT } else { 8000 }
if (Get-Command Get-FinMarkAvailablePort -ErrorAction SilentlyContinue) {
  $port = Get-FinMarkAvailablePort -PreferredPorts @($preferredPort) -FallbackStart 18000 -Label "backend-api"
  Set-FinMarkFrontendApiUrl -ProjectRoot $projectRoot -GatewayPort $port
} else {
  $port = $preferredPort
}

Write-Host ("Starting legacy single-app backend on http://127.0.0.1:{0}" -f $port) -ForegroundColor Green
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port $port
