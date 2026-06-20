Write-Host "Starting FinMark LOCAL 3-node microservice deployment without Docker..." -ForegroundColor Cyan
Write-Host "This starts 4 microservices x 3 nodes = 12 Uvicorn processes, plus a Python API gateway on port 8000." -ForegroundColor Yellow
Write-Host ""

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        Write-Host "Python was not found. Install Python or create .venv first." -ForegroundColor Red
        exit 1
    }
    $python = $pythonCommand.Source
}

$logDir = Join-Path $projectRoot "logs\microservices"
$pidsDir = Join-Path $projectRoot ".microservices"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path $pidsDir | Out-Null
$pidFile = Join-Path $pidsDir "local-pids.csv"
"name,port,pid,app" | Set-Content -Path $pidFile -Encoding UTF8

Write-Host "Initializing/upgrading local database once before starting replicas..." -ForegroundColor Cyan
$env:DEPLOYMENT_MODE = "local-process-microservices"
$env:SERVICE_REPLICAS = "3"
$env:AUTO_CREATE_DB = "true"
$env:SEED_DEMO_DATA = "true"
& $python -m backend.scripts.init_service_database
if ($LASTEXITCODE -ne 0) {
    Write-Host "Database initialization failed. Check your .env MySQL settings." -ForegroundColor Red
    exit $LASTEXITCODE
}

function Start-FinMarkNode {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$App,
        [Parameter(Mandatory=$true)][int]$Port
    )

    $logFile = Join-Path $logDir "$Name.log"
    $command = "set SERVICE_INSTANCE_NAME=$Name && set DEPLOYMENT_MODE=local-process-microservices && set SERVICE_REPLICAS=3 && set AUTO_CREATE_DB=false && set SEED_DEMO_DATA=false && `"$python`" -m uvicorn $App --host 127.0.0.1 --port $Port --log-level info > `"$logFile`" 2>&1"
    $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $command -PassThru -WindowStyle Hidden
    "$Name,$Port,$($process.Id),$App" | Add-Content -Path $pidFile -Encoding UTF8
    Write-Host ("Started {0} on http://127.0.0.1:{1}  PID={2}" -f $Name, $Port, $process.Id) -ForegroundColor Green
}

# Auth/Login Service nodes
Start-FinMarkNode -Name "auth-service-1" -App "backend.microservices.auth_main:app" -Port 8101
Start-FinMarkNode -Name "auth-service-2" -App "backend.microservices.auth_main:app" -Port 8102
Start-FinMarkNode -Name "auth-service-3" -App "backend.microservices.auth_main:app" -Port 8103

# Order Service nodes
Start-FinMarkNode -Name "order-service-1" -App "backend.microservices.order_main:app" -Port 8201
Start-FinMarkNode -Name "order-service-2" -App "backend.microservices.order_main:app" -Port 8202
Start-FinMarkNode -Name "order-service-3" -App "backend.microservices.order_main:app" -Port 8203

# Inventory Service nodes
Start-FinMarkNode -Name "inventory-service-1" -App "backend.microservices.inventory_main:app" -Port 8301
Start-FinMarkNode -Name "inventory-service-2" -App "backend.microservices.inventory_main:app" -Port 8302
Start-FinMarkNode -Name "inventory-service-3" -App "backend.microservices.inventory_main:app" -Port 8303

# Notification Service nodes
Start-FinMarkNode -Name "notification-service-1" -App "backend.microservices.notification_main:app" -Port 8401
Start-FinMarkNode -Name "notification-service-2" -App "backend.microservices.notification_main:app" -Port 8402
Start-FinMarkNode -Name "notification-service-3" -App "backend.microservices.notification_main:app" -Port 8403

# Local gateway node
Start-FinMarkNode -Name "local-api-gateway-1" -App "backend.local_gateway:app" -Port 8000

Write-Host ""
Write-Host "Waiting a few seconds for services to boot..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Gateway health: http://127.0.0.1:8000/api/v1/health" -ForegroundColor Green
Write-Host "Gateway readiness: http://127.0.0.1:8000/api/v1/ready" -ForegroundColor Green
Write-Host "Service info: http://127.0.0.1:8000/api/v1/service-info" -ForegroundColor Green
Write-Host "Frontend dev server still runs with: cd frontend; npm install; npm run dev" -ForegroundColor Green
Write-Host ""
Write-Host "Logs are saved in: logs\microservices" -ForegroundColor Cyan
Write-Host "PID file: .microservices\local-pids.csv" -ForegroundColor Cyan
Write-Host ""
Write-Host "Failover test example without Docker:" -ForegroundColor Yellow
Write-Host "  Stop-Process -Id (Import-Csv .microservices\local-pids.csv | Where-Object name -eq 'order-service-1').pid"
Write-Host "  curl http://127.0.0.1:8000/api/v1/service-info"
Write-Host "  Requests to /api/v1/orders will continue through order-service-2 and order-service-3."
