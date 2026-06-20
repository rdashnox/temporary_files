Write-Host "Stopping FinMark LOCAL microservice processes..." -ForegroundColor Cyan
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $projectRoot ".microservices\local-pids.csv"

if (-not (Test-Path $pidFile)) {
    Write-Host "No local PID file found. Nothing to stop." -ForegroundColor Yellow
    exit 0
}

$rows = Import-Csv $pidFile
foreach ($row in $rows) {
    try {
        $processId = [int]$row.pid
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Stop-Process -Id $processId -Force
            Write-Host ("Stopped {0} PID={1}" -f $row.name, $processId) -ForegroundColor Green
        }
    }
    catch {
        Write-Host ("Could not stop {0} PID={1}" -f $row.name, $row.pid) -ForegroundColor Yellow
    }
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
Write-Host "Local microservice processes stopped." -ForegroundColor Green
