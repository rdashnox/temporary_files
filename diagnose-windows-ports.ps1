Write-Host "FinMark Windows Port Diagnostic" -ForegroundColor Cyan
Write-Host "This helps diagnose [WinError 10013] and port conflicts." -ForegroundColor Yellow
Write-Host ""

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$portHelper = Join-Path $projectRoot "scripts\windows-port-utils.ps1"
if (Test-Path $portHelper) { . $portHelper }

$portsToCheck = @(8000, 8101, 8102, 8103, 8201, 8202, 8203, 8301, 8302, 8303, 8401, 8402, 8403, 18000, 18101, 18201, 18301, 18401)
Write-Host "Port bind test on 127.0.0.1:" -ForegroundColor Cyan
foreach ($port in $portsToCheck) {
    $ok = Test-FinMarkPortAvailable -Port $port -IgnoreReserved
    if ($ok) {
        Write-Host ("  {0}: available" -f $port) -ForegroundColor Green
    }
    else {
        Write-Host ("  {0}: blocked/reserved/in-use" -f $port) -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Processes currently listening on common FinMark ports:" -ForegroundColor Cyan
foreach ($port in $portsToCheck) {
    cmd /c "netstat -ano | findstr :$port" 2>$null
}

Write-Host ""
Write-Host "Windows excluded TCP port ranges:" -ForegroundColor Cyan
netsh interface ipv4 show excludedportrange protocol=tcp

Write-Host ""
Write-Host "Recommended fix:" -ForegroundColor Green
Write-Host "  .\stop-microservices-local.ps1"
Write-Host "  .\start-microservices-local.ps1"
Write-Host "The fixed startup script automatically chooses fallback ports when Windows blocks 8000/8101/etc."
