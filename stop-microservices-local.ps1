Write-Host "Stopping FinMark LOCAL microservice processes..." -ForegroundColor Cyan
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $projectRoot ".microservices\local-pids.csv"

function Stop-FinMarkStaleUvicornProcesses {
    Write-Host "Checking for stale FinMark Uvicorn microservice processes..." -ForegroundColor Cyan
    $processes = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and ($_.CommandLine -like "*uvicorn*") -and (
            ($_.CommandLine -like "*backend.microservices.*") -or
            ($_.CommandLine -like "*backend.local_gateway:app*")
        )
    }
    foreach ($proc in $processes) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
            Write-Host ("Stopped stale Uvicorn process PID={0}" -f $proc.ProcessId) -ForegroundColor Green
        }
        catch {
            Write-Host ("Could not stop stale Uvicorn process PID={0}" -f $proc.ProcessId) -ForegroundColor Yellow
        }
    }
}

if (Test-Path $pidFile) {
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
}
else {
    Write-Host "No local PID file found. Checking for stale FinMark Uvicorn processes anyway..." -ForegroundColor Yellow
}

Stop-FinMarkStaleUvicornProcesses
Write-Host "Local microservice processes stopped." -ForegroundColor Green
