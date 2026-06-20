$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (!(Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "Checking enterprise migration dependencies..." -ForegroundColor Cyan
& $python -c "import alembic" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Alembic is missing. Installing requirements.txt first..." -ForegroundColor Yellow
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt
}

$modeArgs = @()
if ($args.Count -eq 0) {
    Write-Host "No arguments supplied. Using --local for no-Docker local development." -ForegroundColor Yellow
    $modeArgs += "--local"
} else {
    $modeArgs += $args
}

& $python -m backend.enterprise.scripts.run_enterprise_migrations @modeArgs
