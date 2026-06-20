param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 3306,
    [string]$AppUser = "finmark_app",
    [string]$AppPassword = "FinmarkApp@2026!"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Repairing .env for FinMark enterprise four-database MySQL mode..." -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "sync-enterprise-env-app-user.ps1") -HostName $HostName -Port $Port -AppUser $AppUser -AppPassword $AppPassword
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Done. Verify MySQL connectivity with: .\diagnose-mysql-connection.ps1" -ForegroundColor Green
Write-Host "Then verify database tables with: .\verify-enterprise-mysql-databases.ps1" -ForegroundColor Green
