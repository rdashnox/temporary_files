param(
    [switch]$Full
)

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

Write-Host "Cleaning local runtime artifacts that should not be carried across ZIP updates..." -ForegroundColor Cyan

if (Test-Path ".\stop-microservices-local.ps1") { .\stop-microservices-local.ps1 }
if (Test-Path ".\stop-frontend.ps1") { .\stop-frontend.ps1 }

$paths = @(
    ".microservices",
    ".frontend",
    "logs\microservices",
    "backend\__pycache__",
    ".pytest_cache"
)

if ($Full) {
    Write-Host "Full cleanup enabled. This also removes the Python virtual environment and frontend node_modules." -ForegroundColor Yellow
    $paths += @(
        ".venv",
        "frontend\node_modules",
        "frontend\dist"
    )
}

foreach ($path in $paths) {
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
        if (Test-Path $path) {
            Write-Host "Could not remove $path. Close terminals/editors using it, then run this again." -ForegroundColor Yellow
        }
        else {
            Write-Host "Removed $path" -ForegroundColor Green
        }
    }
}

Write-Host "Runtime cleanup finished." -ForegroundColor Green
if ($Full) {
    Write-Host "Run .\install-enterprise-deps.ps1 and cd frontend; npm install after full cleanup." -ForegroundColor Yellow
}
else {
    Write-Host "Use -Full if you need to remove stale .venv and frontend\node_modules after overwriting the project folder." -ForegroundColor Yellow
}
