$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

Write-Host "Stopping stale FinMark frontend/Vite processes..." -ForegroundColor Cyan
$projectPath = (Resolve-Path $PSScriptRoot).Path
$nodeProcesses = Get-CimInstance Win32_Process -Filter "name = 'node.exe'" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -and ($_.CommandLine -like "*vite*" -or $_.CommandLine -like "*frontend*") -and $_.CommandLine -like "*$projectPath*"
}

foreach ($proc in $nodeProcesses) {
    try {
        Write-Host "Stopping node.exe PID=$($proc.ProcessId)"
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    } catch {}
}

Write-Host "Frontend process cleanup complete." -ForegroundColor Green
