$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (!(Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "Installing/updating enterprise backend dependencies..." -ForegroundColor Cyan
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

Write-Host "Enterprise dependencies are ready." -ForegroundColor Green
Write-Host "You can now run:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\python.exe -m backend.enterprise.scripts.run_enterprise_migrations --local" -ForegroundColor White
