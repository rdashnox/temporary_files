param(
    [string]$HostName = "",
    [int]$Port = 0,
    [switch]$StartIfStopped,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. (Join-Path $PSScriptRoot "scripts\mysql-connection-utils.ps1")

if (-not $HostName -or $Port -le 0) {
    $endpoint = Get-FinMarkEnterpriseMySqlEndpoint -EnvPath (Join-Path $PSScriptRoot ".env")
    if (-not $HostName) { $HostName = $endpoint.HostName }
    if ($Port -le 0) { $Port = $endpoint.Port }
    if (-not $Quiet) {
        Write-Host "MySQL endpoint from $($endpoint.Source): $($HostName):$Port" -ForegroundColor Cyan
    }
}

if (-not $Quiet) {
    Write-Host "Testing MySQL TCP connection at $($HostName):$Port..." -ForegroundColor Cyan
}

$ready = Test-FinMarkTcpPort -HostName $HostName -Port $Port
if (-not $ready -and $StartIfStopped) {
    if (-not $Quiet) { Write-Host "MySQL port is not reachable. Checking local Windows MySQL/MariaDB services..." -ForegroundColor Yellow }
    Start-FinMarkPossibleMySqlServices
    Start-Sleep -Seconds 3
    $ready = Test-FinMarkTcpPort -HostName $HostName -Port $Port
}

if ($ready) {
    if (-not $Quiet) { Write-Host "MySQL TCP port is reachable at $($HostName):$Port." -ForegroundColor Green }
    exit 0
}

$services = @(Get-FinMarkMySqlServices)
if (-not $Quiet) {
    if ($services.Count -gt 0) {
        Write-Host "Detected MySQL-related Windows services:" -ForegroundColor Cyan
        foreach ($svc in $services) {
            Write-Host "  $($svc.Name) - $($svc.Status) - $($svc.DisplayName)"
        }
    }
    else {
        Write-Host "No MySQL/MariaDB Windows service was detected by Get-Service." -ForegroundColor Yellow
        Write-Host "If you installed MySQL through XAMPP or Laragon, start it from that control panel."
    }
    Show-FinMarkMySqlConnectionGuidance -HostName $HostName -Port $Port
}
exit 1
