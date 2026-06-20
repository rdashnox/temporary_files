Write-Host "Clearing unlocked FinMark microservice logs..." -ForegroundColor Cyan
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $projectRoot "logs\microservices"
if (-not (Test-Path $logDir)) {
    Write-Host "No logs\microservices folder found." -ForegroundColor Yellow
    exit 0
}

$removed = 0
$locked = 0
Get-ChildItem -Path $logDir -File -Filter "*.log" | ForEach-Object {
    try {
        Remove-Item $_.FullName -Force -ErrorAction Stop
        $removed += 1
    }
    catch {
        $locked += 1
        Write-Host ("Skipped locked log: {0}" -f $_.Name) -ForegroundColor Yellow
    }
}

Write-Host ("Removed {0} log file(s). Skipped {1} locked log file(s)." -f $removed, $locked) -ForegroundColor Green
if ($locked -gt 0) {
    Write-Host "Close VS Code/Notepad terminals or run .\stop-microservices-local.ps1, then try again." -ForegroundColor Yellow
}
