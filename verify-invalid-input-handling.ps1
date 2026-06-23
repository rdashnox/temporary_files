param(
    [string]$ApiBase = "http://127.0.0.1:18000/api/v1"
)

$ErrorActionPreference = "Stop"

function Invoke-ExpectValidationError {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Uri,
        [hashtable]$Headers = @{},
        [object]$Body = $null,
        [string]$ContentType = "application/json"
    )

    Write-Host "`nTesting invalid input: $Name" -ForegroundColor Cyan
    try {
        $params = @{ Method = $Method; Uri = $Uri; Headers = $Headers }
        if ($null -ne $Body) {
            $params.ContentType = $ContentType
            $params.Body = if ($ContentType -eq "application/json") { $Body | ConvertTo-Json -Depth 20 } else { $Body }
        }
        $response = Invoke-RestMethod @params
        Write-Host "FAIL: Request succeeded unexpectedly." -ForegroundColor Red
        $response | ConvertTo-Json -Depth 10
        exit 1
    } catch {
        $statusCode = $null
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        if ($statusCode -in 400, 401, 403, 404, 409, 422) {
            Write-Host "PASS: Returned controlled client error HTTP $statusCode, not a crash." -ForegroundColor Green
            return
        }
        Write-Host "FAIL: Unexpected server/runtime error." -ForegroundColor Red
        Write-Host $_.Exception.Message
        exit 1
    }
}

Write-Host "Enterprise invalid-input validation test against: $ApiBase" -ForegroundColor Yellow

Invoke-ExpectValidationError `
    -Name "Login with missing email/password" `
    -Method Post `
    -Uri "$ApiBase/auth/token" `
    -ContentType "application/x-www-form-urlencoded" `
    -Body "username=&password="

Invoke-ExpectValidationError `
    -Name "Register with missing fields" `
    -Method Post `
    -Uri "$ApiBase/auth/register" `
    -Body @{}

$login = Invoke-RestMethod `
  -Method Post `
  -Uri "$ApiBase/auth/token" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "username=admin@example.com&password=Admin@12345"

$headers = @{ Authorization = "Bearer $($login.access_token)" }

Invoke-ExpectValidationError `
    -Name "Checkout with missing customer data and empty items" `
    -Method Post `
    -Uri "$ApiBase/orders/checkout" `
    -Headers $headers `
    -Body @{ items = @(); customer_name = $null; delivery_address = ""; payment_method = "Cash on Delivery" }

Invoke-ExpectValidationError `
    -Name "Checkout with duplicate product IDs" `
    -Method Post `
    -Uri "$ApiBase/orders/checkout" `
    -Headers $headers `
    -Body @{ items = @(@{ product_id = 1; quantity = 1 }, @{ product_id = 1; quantity = 2 }); customer_name = "Demo Customer"; delivery_address = "123 FinMark Street"; payment_method = "Cash on Delivery" }

Invoke-ExpectValidationError `
    -Name "Order edit with invalid item payload" `
    -Method Put `
    -Uri "$ApiBase/orders/1" `
    -Headers $headers `
    -Body @{ customer_name = "Demo Customer"; delivery_address = "123 FinMark Street"; status = "SHIPPED"; items = @(@{ product_id = 1; product_name = ""; quantity = 0; unit_price = -1 }) }

Invoke-ExpectValidationError `
    -Name "Notification event with missing event_id" `
    -Method Post `
    -Uri "$ApiBase/notifications/internal/events" `
    -Headers @{ "X-Service-Token" = "invalid-demo-token" } `
    -Body @{ event_type = "order.updated"; payload = @{} }

Write-Host "`nPASS: Invalid and missing input cases are handled with controlled error responses." -ForegroundColor Green
