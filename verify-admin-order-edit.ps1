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
        if ($health) { return $true }
    } catch { return $false }
    return $false
}

function Get-FinMarkApiBaseCandidates {
    $candidates = New-Object System.Collections.ArrayList
    if ($ApiBase) { Add-FinMarkCandidate -Candidates $candidates -Url $ApiBase }

    $apiBaseFile = Join-Path $projectRoot ".microservices\api-base-url.txt"
    if (Test-Path $apiBaseFile) {
        $value = (Get-Content $apiBaseFile -ErrorAction SilentlyContinue | Select-Object -First 1)
        Add-FinMarkCandidate -Candidates $candidates -Url $value
    }

    $pidFile = Join-Path $projectRoot ".microservices\local-pids.csv"
    if (Test-Path $pidFile) {
        try {
            $rows = Import-Csv $pidFile
            foreach ($row in $rows) {
                if ($row.name -like "local-api-gateway*" -and $row.port) {
                    Add-FinMarkCandidate -Candidates $candidates -Url "http://127.0.0.1:$($row.port)/api/v1"
                }
            }
        } catch { }
    }

    $frontendEnv = Join-Path $projectRoot "frontend\.env.local"
    if (Test-Path $frontendEnv) {
        $line = Get-Content $frontendEnv -ErrorAction SilentlyContinue | Where-Object { $_ -match '^VITE_API_BASE_URL=' } | Select-Object -First 1
        if ($line) { Add-FinMarkCandidate -Candidates $candidates -Url (($line -replace '^VITE_API_BASE_URL=', '').Trim()) }
    }

    Add-FinMarkCandidate -Candidates $candidates -Url "http://127.0.0.1:8000/api/v1"
    for ($port = 18000; $port -le 18030; $port++) { Add-FinMarkCandidate -Candidates $candidates -Url "http://127.0.0.1:$port/api/v1" }
    return $candidates
}

function Get-FinMarkRunningApiBaseUrl {
    foreach ($candidate in (Get-FinMarkApiBaseCandidates)) {
        if (Test-FinMarkGateway -BaseUrl $candidate) { return $candidate }
    }
    return ""
}

function Resolve-FinMarkListResponse {
    param($Value)
    if ($null -eq $Value) { return @() }
    $propertyNames = @($Value.PSObject.Properties | ForEach-Object { $_.Name })
    if ($propertyNames -contains "items") { return @($Value.items) }
    if ($propertyNames -contains "data") { return @($Value.data) }
    return @($Value)
}

function Invoke-FinMarkJson {
    param([string]$Method, [string]$Uri, [hashtable]$Headers = $null, [string]$ContentType = $null, $Body = $null)
    try {
        $params = @{ Method = $Method; Uri = $Uri; TimeoutSec = 20 }
        if ($Headers) { $params.Headers = $Headers }
        if ($ContentType) { $params.ContentType = $ContentType }
        if ($null -ne $Body) { $params.Body = $Body }
        return Invoke-RestMethod @params
    } catch {
        Write-Host "Request failed: $Method $Uri" -ForegroundColor Red
        if ($_.Exception.Response) {
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $errorBody = $reader.ReadToEnd()
                if ($errorBody) { Write-Host $errorBody -ForegroundColor DarkYellow }
            } catch { }
        }
        Show-FinMarkOrderServiceErrorLogs
        throw
    }
}

function Show-FinMarkOrderServiceErrorLogs {
    $logDir = Join-Path $projectRoot "logs\microservices"
    if (-not (Test-Path $logDir)) { return }
    $logs = Get-ChildItem $logDir -Filter "order-service-*.err.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3
    if (-not $logs) { return }
    Write-Host "`nLatest Order Service error log lines:" -ForegroundColor Yellow
    foreach ($log in $logs) {
        Write-Host ("--- {0} ---" -f $log.Name) -ForegroundColor DarkYellow
        Get-Content $log.FullName -Tail 30 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ -ForegroundColor DarkYellow }
    }
}

$apiBase = Get-FinMarkRunningApiBaseUrl
if (-not $apiBase -and $StartIfDown) {
    Write-Host "No running local API gateway was found. Starting local enterprise microservices first..." -ForegroundColor Yellow
    & (Join-Path $projectRoot "start-microservices-local-mysql.ps1")
    Start-Sleep -Seconds 8
    $apiBase = Get-FinMarkRunningApiBaseUrl
}

if (-not $apiBase) {
    Write-Host "Unable to connect to the local API gateway." -ForegroundColor Red
    Write-Host "Run .\start-microservices-local-mysql.ps1 first, then run this verifier again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Testing Admin order edit/update flow against: $apiBase" -ForegroundColor Cyan
$form = "username=admin%40example.com&password=Admin%4012345"
$tokenResponse = Invoke-FinMarkJson -Method Post -Uri "$apiBase/auth/token" -ContentType "application/x-www-form-urlencoded" -Body $form
$headers = @{ Authorization = "Bearer $($tokenResponse.access_token)" }

$productsResponse = Invoke-FinMarkJson -Method Get -Uri "$apiBase/inventory/products" -Headers $headers
$products = Resolve-FinMarkListResponse -Value $productsResponse
if (-not $products -or $products.Count -lt 1) { throw "No inventory products found. Run .\seed-enterprise-mysql.ps1 first." }
$product = $products[0]

$idempotencyKey = "verify-admin-order-edit-$([guid]::NewGuid().ToString('N'))"
$checkoutPayload = @{
    customer_name = "Admin Order Edit Verification"
    delivery_address = "FinMark Edit Verification Address"
    payment_method = "Cash on Delivery"
    coupon_code = ""
    idempotency_key = $idempotencyKey
    items = @(@{ product_id = [int]$product.id; quantity = 1 })
} | ConvertTo-Json -Depth 8

$checkoutHeaders = $headers.Clone()
$checkoutHeaders["Idempotency-Key"] = $idempotencyKey
$order = Invoke-FinMarkJson -Method Post -Uri "$apiBase/orders/checkout" -Headers $checkoutHeaders -ContentType "application/json" -Body $checkoutPayload
Write-Host "Checkout created order: $($order.order_id)" -ForegroundColor Green

$orders = Resolve-FinMarkListResponse -Value (Invoke-FinMarkJson -Method Get -Uri "$apiBase/orders?limit=100&search=$($order.order_id)" -Headers $headers)
$matched = $orders | Where-Object { $_.order_number -eq $order.order_id } | Select-Object -First 1
if (-not $matched) { throw "Created order was not returned by /orders search." }

$editPayload = @{
    customer_name = $matched.customer_name
    delivery_address = $matched.delivery_address
    payment_method = $matched.payment_method
    status = "SHIPPED"
    discount = [decimal]$matched.discount
    shipping_fee = [decimal]$matched.shipping_fee
    tax = [decimal]$matched.tax
    items = @($matched.items | ForEach-Object {
        @{ product_id = [int]$_.product_id; product_name = [string]$_.product_name; quantity = [int]$_.quantity; unit_price = [decimal]$_.unit_price }
    })
} | ConvertTo-Json -Depth 8

$updated = Invoke-FinMarkJson -Method Put -Uri "$apiBase/orders/$($matched.id)" -Headers $headers -ContentType "application/json" -Body $editPayload
if ($updated.status -ne "SHIPPED") { throw "Order update did not persist. Expected SHIPPED but got $($updated.status)." }
Write-Host "PASS: Admin Order Edit successfully updated order $($updated.order_number) to status $($updated.status)." -ForegroundColor Green

try {
    $notifications = Resolve-FinMarkListResponse -Value (Invoke-FinMarkJson -Method Get -Uri "$apiBase/notifications?limit=20" -Headers $headers)
    $editNotice = $notifications | Where-Object {
        ($_.title -match "Order updated") -and ($_.entity_id -eq $updated.order_number -or $_.message -match $updated.order_number)
    } | Select-Object -First 1
    if ($editNotice) {
        Write-Host "PASS: Order edit notification is available: $($editNotice.title) - $($editNotice.message)" -ForegroundColor Green
    } else {
        Write-Host "NOTICE: The order update passed. No persisted notification was found yet. Restart microservices so NOTIFICATION_SERVICE_URL is applied, or run the RabbitMQ notification worker in Docker/cloud mode." -ForegroundColor Yellow
    }
} catch {
    Write-Host "NOTICE: The order update passed. Notification check could not complete: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "Open Admin Dashboard > Orders > Refresh. Edit should now focus the edit panel and show an edit notification." -ForegroundColor Green
