Write-Host "Starting FinMark 3-node microservice deployment..." -ForegroundColor Cyan
Write-Host "Preferred mode: Docker Compose with 4 microservices x 3 nodes = 12 FastAPI containers, plus MySQL and Nginx gateway." -ForegroundColor Yellow
Write-Host ""

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue

if (-not $dockerCommand) {
    Write-Host "Docker was not found on this computer." -ForegroundColor Yellow
    Write-Host "Using the no-Docker local fallback instead." -ForegroundColor Yellow
    Write-Host "This starts 12 local Uvicorn service processes plus a Python API gateway." -ForegroundColor Yellow
    Write-Host ""
    & .\start-microservices-local.ps1
    exit $LASTEXITCODE
}

try {
    docker info *> $null
    if ($LASTEXITCODE -ne 0) { throw "Docker daemon is not responding." }
}
catch {
    Write-Host "Docker is installed, but Docker Desktop/daemon is not running." -ForegroundColor Yellow
    Write-Host "Using the no-Docker local fallback instead." -ForegroundColor Yellow
    Write-Host ""
    & .\start-microservices-local.ps1
    exit $LASTEXITCODE
}

docker compose -f docker-compose.microservices.yml up --build -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker Compose failed. You can still run the local fallback:" -ForegroundColor Yellow
    Write-Host "  .\start-microservices-local.ps1" -ForegroundColor White
    exit $LASTEXITCODE
}

Write-Host "" 
Write-Host "Containers:" -ForegroundColor Cyan
docker compose -f docker-compose.microservices.yml ps

Write-Host "" 
Write-Host "API Gateway: http://127.0.0.1:8000/api/v1/health" -ForegroundColor Green
Write-Host "Frontend dev server still runs with: cd frontend; npm run dev" -ForegroundColor Green
Write-Host "" 
Write-Host "Failover test example:" -ForegroundColor Yellow
Write-Host "  docker compose -f docker-compose.microservices.yml stop order-service-1"
Write-Host "  curl http://127.0.0.1:8000/api/v1/service-info"
Write-Host "  docker compose -f docker-compose.microservices.yml start order-service-1"
