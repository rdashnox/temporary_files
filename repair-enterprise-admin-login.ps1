$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$pythonExe = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (!(Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "Repairing and verifying enterprise demo admin login..."
& $pythonExe -m backend.enterprise.scripts.repair_admin_login
if ($LASTEXITCODE -ne 0) {
    throw "Admin login repair failed. Check Auth DB connectivity and migrations."
}

Write-Host ""
Write-Host "Now use:"
Write-Host "  .\start-microservices-local-mysql.ps1"
Write-Host "  .\start-frontend.ps1"
Write-Host ""
Write-Host "Login:"
Write-Host "  admin@example.com"
Write-Host "  Admin@12345"
