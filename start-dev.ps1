$ErrorActionPreference = "Stop"

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$PSScriptRoot\start-backend.ps1`""
Start-Sleep -Seconds 4
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$PSScriptRoot\start-frontend.ps1`""

Write-Host "Opened backend and frontend terminals."
Write-Host "Backend:  http://127.0.0.1:8000/docs"
Write-Host "Frontend: http://127.0.0.1:5173"
