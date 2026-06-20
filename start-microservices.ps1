Write-Host "Starting FinMark ENTERPRISE 3-node microservice deployment..." -ForegroundColor Cyan
Write-Host "Preferred mode: Docker Compose with 4 microservices x 3 nodes = 12 FastAPI containers, 4 separate MySQL databases, RabbitMQ, Jaeger, and Nginx gateway." -ForegroundColor Yellow
Write-Host ""

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$portHelper = Join-Path $projectRoot "scripts\windows-port-utils.ps1"
if (Test-Path $portHelper) { . $portHelper }

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

$gatewayPort = if ($env:FINMARK_GATEWAY_PORT) { [int]$env:FINMARK_GATEWAY_PORT } else { 8000 }
if (Get-Command Get-FinMarkAvailablePort -ErrorAction SilentlyContinue) {
    $gatewayPort = Get-FinMarkAvailablePort -PreferredPorts @($gatewayPort) -FallbackStart 18000 -Label "docker-nginx-gateway"
    $env:FINMARK_GATEWAY_PORT = "$gatewayPort"
    Set-FinMarkFrontendApiUrl -ProjectRoot $projectRoot -GatewayPort $gatewayPort
}

Write-Host ("Docker gateway host port: {0}" -f $gatewayPort) -ForegroundColor Cyan
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
Write-Host ("API Gateway: http://127.0.0.1:{0}/api/v1/health" -f $gatewayPort) -ForegroundColor Green
Write-Host "Frontend dev server still runs with: cd frontend; npm install; npm run dev" -ForegroundColor Green
if ($gatewayPort -ne 8000) {
    Write-Host "Because port 8000 was unavailable, restart the frontend so Vite reads frontend\.env.local." -ForegroundColor Yellow
}
Write-Host "" 
Write-Host "Failover test example:" -ForegroundColor Yellow
Write-Host "  docker compose -f docker-compose.microservices.yml stop order-service-1"
Write-Host ("  curl http://127.0.0.1:{0}/api/v1/service-info" -f $gatewayPort)
Write-Host "  docker compose -f docker-compose.microservices.yml start order-service-1"
