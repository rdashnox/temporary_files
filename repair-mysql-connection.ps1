param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 3306,
    [switch]$StartIfStopped,
    [switch]$SkipEnvRepair
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "FinMark MySQL connection repair" -ForegroundColor Cyan
Write-Host "Target MySQL server: $($HostName):$Port" -ForegroundColor Cyan

if (-not $SkipEnvRepair) {
    Write-Host "Repairing enterprise .env database URLs for this host/port..." -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "repair-enterprise-env.ps1") -HostName $HostName -Port $Port
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& (Join-Path $PSScriptRoot "diagnose-mysql-connection.ps1") -HostName $HostName -Port $Port -StartIfStopped:$StartIfStopped
if ($LASTEXITCODE -ne 0) {
    Write-Host "MySQL is still not reachable. Start MySQL Server from Services/XAMPP/Laragon, then run this command again." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "MySQL TCP connection is ready." -ForegroundColor Green
Write-Host "Next commands:" -ForegroundColor Cyan
Write-Host "  .\setup-enterprise-mysql.ps1 -HostName $HostName -Port $Port"
Write-Host "  .\run-enterprise-migrations-mysql.ps1"
Write-Host "  .\seed-enterprise-mysql.ps1"
Write-Host "  .\start-microservices-local-mysql.ps1"
