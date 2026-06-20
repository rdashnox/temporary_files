Write-Host "Stopping FinMark microservice deployment..." -ForegroundColor Cyan

if (Test-Path ".\stop-microservices-local.ps1") {
    & .\stop-microservices-local.ps1
}

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCommand) {
    try {
        docker info *> $null
        if ($LASTEXITCODE -eq 0) {
            docker compose -f docker-compose.microservices.yml down
        }
    }
    catch {
        Write-Host "Docker is not running; skipped Docker Compose shutdown." -ForegroundColor Yellow
    }
}
else {
    Write-Host "Docker is not installed; skipped Docker Compose shutdown." -ForegroundColor Yellow
}
