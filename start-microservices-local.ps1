param(
    [switch]$UseMySQL
)

Write-Host "Starting FinMark LOCAL ENTERPRISE 3-node microservice deployment without Docker..." -ForegroundColor Cyan
Write-Host "This starts 4 enterprise microservices x 3 nodes = 12 Uvicorn processes, plus a Python API gateway." -ForegroundColor Yellow
Write-Host ""

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Import-FinMarkDotEnvFile {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (!(Test-Path $Path)) { return }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { return }
        $key = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}


$portHelper = Join-Path $projectRoot "scripts\windows-port-utils.ps1"
if (Test-Path $portHelper) {
    . $portHelper
}
else {
    Write-Host "Missing scripts\windows-port-utils.ps1. Please re-extract the fixed project ZIP." -ForegroundColor Red
    exit 1
}

$pidsDir = Join-Path $projectRoot ".microservices"
$pidFile = Join-Path $pidsDir "local-pids.csv"
if (Test-Path $pidFile) {
    Write-Host "Previous local microservice PID file found. Stopping old local nodes first..." -ForegroundColor Yellow
    & (Join-Path $projectRoot "stop-microservices-local.ps1")
}
else {
    # Safety cleanup: sometimes Windows keeps old hidden Uvicorn processes even when the PID file is gone.
    # This prevents repeated fallback-port messages when old FinMark nodes are still listening.
    & (Join-Path $projectRoot "stop-microservices-local.ps1") | Out-Null
}

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        Write-Host "Python was not found. Install Python or create .venv first." -ForegroundColor Red
        exit 1
    }
    Write-Host "Creating Python virtual environment for local microservices..." -ForegroundColor Cyan
    & $pythonCommand.Source -m venv .venv
    $python = Join-Path $projectRoot ".venv\Scripts\python.exe"
}

Write-Host "Checking backend dependencies..." -ForegroundColor Cyan
& $python -c "import fastapi, sqlalchemy, uvicorn, alembic, httpx" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Some backend dependencies are missing. Installing requirements.txt..." -ForegroundColor Yellow
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Dependency installation failed. Run .\install-enterprise-deps.ps1 and try again." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

$logDir = Join-Path $projectRoot "logs\microservices"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path $pidsDir | Out-Null
$script:runStamp = Get-Date -Format "yyyyMMdd-HHmmss"
"name,port,pid,app,stdout,stderr" | Set-Content -Path $pidFile -Encoding UTF8

Write-Host "Probing Windows-safe localhost ports before starting Uvicorn..." -ForegroundColor Cyan
$serviceConfigs = @(
    @{ Service = "auth-service";         App = "backend.microservices.auth_main:app";         Preferred = @(8101, 8102, 8103); FallbackStart = 18101 },
    @{ Service = "order-service";        App = "backend.microservices.order_main:app";        Preferred = @(8201, 8202, 8203); FallbackStart = 18201 },
    @{ Service = "inventory-service";    App = "backend.microservices.inventory_main:app";    Preferred = @(8301, 8302, 8303); FallbackStart = 18301 },
    @{ Service = "notification-service"; App = "backend.microservices.notification_main:app"; Preferred = @(8401, 8402, 8403); FallbackStart = 18401 }
)

$servicePools = [ordered]@{}
$nodesToStart = @()
foreach ($config in $serviceConfigs) {
    $servicePools[$config.Service] = @()
    for ($i = 0; $i -lt 3; $i++) {
        $nodeNumber = $i + 1
        $label = ("{0}-{1}" -f $config.Service, $nodeNumber)
        $port = Get-FinMarkAvailablePort -PreferredPorts @($config.Preferred[$i]) -FallbackStart ($config.FallbackStart + $i) -Label $label
        $servicePools[$config.Service] += "http://127.0.0.1:$port"
        $nodesToStart += [pscustomobject]@{
            Name = $label
            App = $config.App
            Port = $port
        }
    }
}

$gatewayPort = Get-FinMarkAvailablePort -PreferredPorts @(8000) -FallbackStart 18000 -Label "local-api-gateway"
$gatewayUrl = "http://127.0.0.1:$gatewayPort"
$servicePoolsJson = $servicePools | ConvertTo-Json -Compress -Depth 5

Write-Host ""
Write-Host "Selected local service ports:" -ForegroundColor Cyan
foreach ($serviceName in $servicePools.Keys) {
    Write-Host ("  {0}: {1}" -f $serviceName, (($servicePools[$serviceName]) -join ", ")) -ForegroundColor White
}
Write-Host ("  local-api-gateway: {0}" -f $gatewayUrl) -ForegroundColor White

Set-FinMarkFrontendApiUrl -ProjectRoot $projectRoot -GatewayPort $gatewayPort
$apiBaseUrlFile = Join-Path $pidsDir "api-base-url.txt"
$gatewayPortFile = Join-Path $pidsDir "gateway-port.txt"
Set-Content -Path $apiBaseUrlFile -Value ("{0}/api/v1" -f $gatewayUrl) -Encoding UTF8
Set-Content -Path $gatewayPortFile -Value $gatewayPort -Encoding UTF8

Write-Host ""
if ($UseMySQL) {
    Write-Host "Using four dedicated MySQL databases from .env for local microservice mode..." -ForegroundColor Cyan
    Import-FinMarkDotEnvFile -Path (Join-Path $projectRoot ".env")

    $missingEnterpriseUrls = @()
    foreach ($key in @("AUTH_DATABASE_URL", "ORDER_DATABASE_URL", "INVENTORY_DATABASE_URL", "NOTIFICATION_DATABASE_URL")) {
        if (-not [System.Environment]::GetEnvironmentVariable($key, "Process")) {
            $missingEnterpriseUrls += $key
        }
    }
    if ($missingEnterpriseUrls.Count -gt 0) {
        Write-Host "Missing enterprise MySQL database URL(s) in .env:" -ForegroundColor Red
        foreach ($key in $missingEnterpriseUrls) { Write-Host "  - $key" -ForegroundColor Red }
        Write-Host "Run .\setup-enterprise-mysql.ps1 first." -ForegroundColor Yellow
        exit 1
    }

    $env:ENTERPRISE_MICROSERVICES_ENABLED = "true"
    $env:DEPLOYMENT_MODE = "local-enterprise-microservices-mysql"
    $env:SERVICE_REPLICAS = "3"
    $env:AUTO_CREATE_DB = "false"
    $env:SEED_DEMO_DATA = "false"
    $env:EVENT_BUS_ENABLED = "false"
    $env:OTEL_ENABLED = "false"
    $env:INVENTORY_SERVICE_URL = $gatewayUrl
    $env:SERVICE_POOLS_JSON = $servicePoolsJson

    Write-Host "Checking MySQL database readiness before starting replicas..." -ForegroundColor Cyan
    & $python -m backend.enterprise.scripts.verify_mysql_enterprise_databases
    if ($LASTEXITCODE -ne 0) {
        Write-Host "MySQL verification failed. Run .\setup-enterprise-mysql.ps1 or .\run-enterprise-migrations-mysql.ps1." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}
else {
    Write-Host "Initializing/upgrading separated local SQLite enterprise databases once before starting replicas..." -ForegroundColor Cyan
    Write-Host "Tip: use .\start-microservices-local-mysql.ps1 if you want to use MySQL Workbench databases." -ForegroundColor Yellow
    $dataDir = Join-Path $projectRoot "data\enterprise-local"
    New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

    $env:ENTERPRISE_MICROSERVICES_ENABLED = "true"
    $env:DEPLOYMENT_MODE = "local-enterprise-microservices"
    $env:SERVICE_REPLICAS = "3"
    $env:AUTO_CREATE_DB = "true"
    $env:SEED_DEMO_DATA = "true"
    $env:EVENT_BUS_ENABLED = "false"
    $env:OTEL_ENABLED = "false"
    $env:INVENTORY_SERVICE_URL = $gatewayUrl
    $env:SERVICE_POOLS_JSON = $servicePoolsJson
    if (-not $env:AUTH_DATABASE_URL) { $env:AUTH_DATABASE_URL = "sqlite:///$($dataDir.Replace('\','/'))/auth.db" }
    if (-not $env:ORDER_DATABASE_URL) { $env:ORDER_DATABASE_URL = "sqlite:///$($dataDir.Replace('\','/'))/order.db" }
    if (-not $env:INVENTORY_DATABASE_URL) { $env:INVENTORY_DATABASE_URL = "sqlite:///$($dataDir.Replace('\','/'))/inventory.db" }
    if (-not $env:NOTIFICATION_DATABASE_URL) { $env:NOTIFICATION_DATABASE_URL = "sqlite:///$($dataDir.Replace('\','/'))/notification.db" }

    & $python -m backend.enterprise.scripts.init_enterprise_databases
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Enterprise database initialization failed. Check your .env database settings." -ForegroundColor Red
        exit $LASTEXITCODE
    }

    $env:AUTO_CREATE_DB = "false"
    $env:SEED_DEMO_DATA = "false"
}

function Start-FinMarkNode {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$App,
        [Parameter(Mandatory=$true)][int]$Port
    )

    # Use unique log files for each run. Windows can keep old log files locked
    # when a previous Uvicorn process, VS Code, antivirus, or PowerShell still has
    # a handle open. Creating a fresh file avoids Remove-Item failures and keeps
    # older logs available for debugging.
    $stdoutFile = Join-Path $logDir ("{0}-{1}.out.log" -f $Name, $script:runStamp)
    $stderrFile = Join-Path $logDir ("{0}-{1}.err.log" -f $Name, $script:runStamp)

    $env:SERVICE_INSTANCE_NAME = $Name
    $arguments = @("-m", "uvicorn", $App, "--host", "127.0.0.1", "--port", "$Port", "--log-level", "info")
    $process = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $projectRoot -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 800
    $process.Refresh()

    if ($process.HasExited) {
        Write-Host ("Failed to start {0} on 127.0.0.1:{1}." -f $Name, $Port) -ForegroundColor Red
        if (Test-Path $stderrFile) {
            Write-Host "Last error log lines:" -ForegroundColor Yellow
            Get-Content $stderrFile -Tail 20 | ForEach-Object { Write-Host $_ -ForegroundColor DarkYellow }
        }
        Show-FinMarkWindowsPortHelp
        throw "Startup failed for $Name."
    }

    "$Name,$Port,$($process.Id),$App,$stdoutFile,$stderrFile" | Add-Content -Path $pidFile -Encoding UTF8
    Write-Host ("Started {0} on http://127.0.0.1:{1}  PID={2}" -f $Name, $Port, $process.Id) -ForegroundColor Green
}

foreach ($node in $nodesToStart) {
    Start-FinMarkNode -Name $node.Name -App $node.App -Port $node.Port
}

Start-FinMarkNode -Name "local-api-gateway-1" -App "backend.local_gateway:app" -Port $gatewayPort

Write-Host ""
Write-Host "Waiting a few seconds for services to boot..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

Write-Host ""
Write-Host ("Gateway health: {0}/api/v1/health" -f $gatewayUrl) -ForegroundColor Green
Write-Host ("Gateway readiness: {0}/api/v1/ready" -f $gatewayUrl) -ForegroundColor Green
Write-Host ("Service info: {0}/api/v1/service-info" -f $gatewayUrl) -ForegroundColor Green
Write-Host "Frontend dev server still runs with: cd frontend; npm install; npm run dev" -ForegroundColor Green
if ($gatewayPort -ne 8000) {
    Write-Host "Because port 8000 was unavailable, restart the frontend after this script so Vite reads frontend\.env.local." -ForegroundColor Yellow
    Write-Host "Note: fallback ports are not fatal. They mean another process is already using the preferred port." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Logs are saved in: logs\microservices" -ForegroundColor Cyan
Write-Host "PID file: .microservices\local-pids.csv" -ForegroundColor Cyan
Write-Host ""
Write-Host "Failover test example without Docker:" -ForegroundColor Yellow
Write-Host "  Stop-Process -Id (Import-Csv .microservices\local-pids.csv | Where-Object name -eq 'order-service-1').pid"
Write-Host ("  curl {0}/api/v1/service-info" -f $gatewayUrl)
Write-Host "  Requests to /api/v1/orders will continue through order-service-2 and order-service-3."
Show-FinMarkWindowsPortHelp
