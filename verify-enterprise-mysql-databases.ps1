param(
    [switch]$SkipMysqlProbe,
    [switch]$StartMySQLIfStopped
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
    Write-Host "Missing .venv. Run .\install-enterprise-deps.ps1 first." -ForegroundColor Red
    exit 1
}

if (-not $SkipMysqlProbe) {
    & (Join-Path $PSScriptRoot "diagnose-mysql-connection.ps1") -StartIfStopped:$StartMySQLIfStopped
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& $python -m backend.enterprise.scripts.verify_mysql_enterprise_databases
