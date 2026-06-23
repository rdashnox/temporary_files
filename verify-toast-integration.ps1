$ErrorActionPreference = "Stop"

Write-Host "FinMark Toast Integration Static Verification" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

$checks = @(
    @{ Name = "react-toastify dependency"; Path = "frontend\package.json"; Pattern = "react-toastify" },
    @{ Name = "ToastContainer mounted"; Path = "frontend\src\main.jsx"; Pattern = "ToastContainer" },
    @{ Name = "Toast CSS imported"; Path = "frontend\src\main.jsx"; Pattern = "react-toastify/dist/ReactToastify.css" },
    @{ Name = "Central toast utility"; Path = "frontend\src\utils\toast.js"; Pattern = "showValidationToast" },
    @{ Name = "Login validation toast"; Path = "frontend\src\pages\LoginPage.jsx"; Pattern = "showApiErrorToast" },
    @{ Name = "Checkout toast"; Path = "frontend\src\components\CartPanel.jsx"; Pattern = "showSuccessToast" },
    @{ Name = "Admin edit toast"; Path = "frontend\src\pages\AdminDashboard.jsx"; Pattern = "order-edit-notification" },
    @{ Name = "Global toast event listener"; Path = "frontend\src\App.jsx"; Pattern = "finmark:toast" }
)

$failed = 0
foreach ($check in $checks) {
    if (!(Test-Path $check.Path)) {
        Write-Host "FAIL: $($check.Name) - missing file $($check.Path)" -ForegroundColor Red
        $failed++
        continue
    }

    $match = Select-String -Path $check.Path -Pattern $check.Pattern -SimpleMatch -ErrorAction SilentlyContinue
    if ($match) {
        Write-Host "PASS: $($check.Name)" -ForegroundColor Green
    } else {
        Write-Host "FAIL: $($check.Name) - pattern not found: $($check.Pattern)" -ForegroundColor Red
        $failed++
    }
}

if ($failed -gt 0) {
    throw "$failed toast integration check(s) failed."
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "PASS: Toast integration source checks passed." -ForegroundColor Green
Write-Host "Next runtime demo:" -ForegroundColor Yellow
Write-Host "  .\start-microservices-local-mysql.ps1"
Write-Host "  .\start-frontend.ps1"
Write-Host "  Try empty login, invalid checkout, valid checkout, edit order, and save."
