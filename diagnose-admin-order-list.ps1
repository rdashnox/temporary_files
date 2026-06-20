param(
    [string]$ApiBase = "",
    [switch]$StartIfDown
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Normalize-FinMarkApiBaseUrl {
    param([string]$Value)
    if (-not $Value) { return "" }
    $clean = $Value.Trim().TrimEnd("/")
    if ($clean.EndsWith("/api/v1")) { return $clean }
    if ($clean.EndsWith("/api")) { return "$clean/v1" }
    return "$clean/api/v1"
}

function Add-FinMarkCandidate {
    param([System.Collections.ArrayList]$Candidates, [string]$Url)
    $normalized = Normalize-FinMarkApiBaseUrl -Value $Url
    if ($normalized -and -not $Candidates.Contains($normalized)) { [void]$Candidates.Add($normalized) }
}

function Test-FinMarkGateway {
    param([string]$BaseUrl)
    try {
        $health = Invoke-RestMethod -Method Get -Uri "$BaseUrl/health" -TimeoutSec 3
        return [bool]$health
    } catch { return $false }
}

function Get-FinMarkApiBaseCandidates {
    $candidates = New-Object System.Collections.ArrayList
    if ($ApiBase) { Add-FinMarkCandidate -Candidates $candidates -Url $ApiBase }
    $apiBaseFile = Join-Path $projectRoot ".microservices\api-base-url.txt"
    if (Test-Path $apiBaseFile) { Add-FinMarkCandidate -Candidates $candidates -Url (Get-Content $apiBaseFile | Select-Object -First 1) }
    $frontendEnv = Join-Path $projectRoot "frontend\.env.local"
    if (Test-Path $frontendEnv) {
        $line = Get-Content $frontendEnv -ErrorAction SilentlyContinue | Where-Object { $_ -match '^VITE_API_BASE_URL=' } | Select-Object -First 1
        if ($line) { Add-FinMarkCandidate -Candidates $candidates -Url (($line -replace '^VITE_API_BASE_URL=', '').Trim()) }
    }
    Add-FinMarkCandidate -Candidates $candidates -Url "http://127.0.0.1:8000/api/v1"
    for ($port = 18000; $port -le 18040; $port++) { Add-FinMarkCandidate -Candidates $candidates -Url "http://127.0.0.1:$port/api/v1" }
    return $candidates
}

function Get-FinMarkRunningApiBaseUrl {
    foreach ($candidate in (Get-FinMarkApiBaseCandidates)) {
        if (Test-FinMarkGateway -BaseUrl $candidate) { return $candidate }
    }
    return ""
}

function Invoke-FinMarkJson {
    param([string]$Method, [string]$Uri, [hashtable]$Headers = $null, [string]$ContentType = $null, $Body = $null)
    $params = @{ Method = $Method; Uri = $Uri; TimeoutSec = 20 }
    if ($Headers) { $params.Headers = $Headers }
    if ($ContentType) { $params.ContentType = $ContentType }
    if ($null -ne $Body) { $params.Body = $Body }
    return Invoke-RestMethod @params
}

function Invoke-FinMarkOptionalJson {
    param([string]$Method, [string]$Uri, [hashtable]$Headers = $null, [string]$ContentType = $null, $Body = $null)
    try {
        return Invoke-FinMarkJson -Method $Method -Uri $Uri -Headers $Headers -ContentType $ContentType -Body $Body
    }
    catch {
        $statusCode = $null
        if ($_.Exception.Response) {
            try { $statusCode = [int]$_.Exception.Response.StatusCode } catch { }
        }
        Write-Host "Optional diagnostic request failed: $Method $Uri" -ForegroundColor DarkYellow
        if ($statusCode) { Write-Host "  HTTP status: $statusCode" -ForegroundColor DarkYellow }
        return $null
    }
}

$apiBase = Get-FinMarkRunningApiBaseUrl
if (-not $apiBase -and $StartIfDown) {
    Write-Host "No running gateway found. Starting local enterprise microservices..." -ForegroundColor Yellow
    & (Join-Path $projectRoot "start-microservices-local-mysql.ps1")
    Start-Sleep -Seconds 8
    $apiBase = Get-FinMarkRunningApiBaseUrl
}
if (-not $apiBase) {
    Write-Host "No API gateway is reachable. Run .\start-microservices-local-mysql.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Admin order-list diagnostic against: $apiBase" -ForegroundColor Cyan
$form = "username=admin%40example.com&password=Admin%4012345"
$tokenResponse = Invoke-FinMarkJson -Method Post -Uri "$apiBase/auth/token" -ContentType "application/x-www-form-urlencoded" -Body $form
$headers = @{ Authorization = "Bearer $($tokenResponse.access_token)" }

Write-Host "\n1) Order Service debug summary" -ForegroundColor Yellow
$debug = $null
$debugRoutes = @(
    "$apiBase/orders/debug/summary",
    "$apiBase/orders/debug-summary",
    "$apiBase/orders/summary/debug",
    "$apiBase/database/orders/debug/summary",
    "$apiBase/database/orders/debug-summary"
)
foreach ($route in $debugRoutes) {
    $debug = Invoke-FinMarkOptionalJson -Method Get -Uri $route -Headers $headers
    if ($debug) {
        Write-Host "Debug route succeeded: $route" -ForegroundColor Green
        $debug | ConvertTo-Json -Depth 8
        break
    }
}
if (-not $debug) {
    Write-Host "No debug endpoint is available on the currently running services." -ForegroundColor Yellow
    Write-Host "This usually means old microservice processes are still running. The script will continue by checking the real order-list APIs." -ForegroundColor Yellow
}

Write-Host "\n2) Admin Order List API /orders" -ForegroundColor Yellow
$orders = Invoke-FinMarkOptionalJson -Method Get -Uri "$apiBase/orders?limit=20&_ts=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())" -Headers $headers
if ($orders) {
    $orders | ConvertTo-Json -Depth 8
} else {
    Write-Host "The unfiltered /orders list failed. This commonly happens when old seeded order rows use lowercase status values." -ForegroundColor Yellow
    Write-Host "Run: .\repair-order-statuses.ps1" -ForegroundColor Cyan
}

Write-Host "\n3) Compatibility API /database/orders" -ForegroundColor Yellow
$compatOrders = Invoke-FinMarkOptionalJson -Method Get -Uri "$apiBase/database/orders?limit=20&_ts=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())" -Headers $headers
if ($compatOrders) {
    $compatOrders | ConvertTo-Json -Depth 8
} else {
    Write-Host "Compatibility order list also failed. Run .\repair-order-statuses.ps1, then restart microservices." -ForegroundColor Yellow
}

Write-Host "\n4) Latest order fallback" -ForegroundColor Yellow
$latestOrders = Invoke-FinMarkOptionalJson -Method Get -Uri "$apiBase/orders/latest?limit=10&_ts=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())" -Headers $headers
if ($latestOrders) { $latestOrders | ConvertTo-Json -Depth 8 }

Write-Host "\nIf /orders has rows but the browser shows none, restart frontend and hard-refresh browser:" -ForegroundColor Green
Write-Host "  .\stop-frontend.ps1" -ForegroundColor White
Write-Host "  .\start-frontend.ps1" -ForegroundColor White
Write-Host "  Press Ctrl+F5 in browser" -ForegroundColor White
