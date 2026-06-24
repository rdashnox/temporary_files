$ErrorActionPreference = 'Stop'

Write-Host "Checking Product/Admin dashboards for embedded success/error notification UI..." -ForegroundColor Cyan

$files = @(
  "frontend\src\components\CartPanel.jsx",
  "frontend\src\pages\CartDashboard.jsx",
  "frontend\src\pages\AdminDashboard.jsx"
)

$patterns = @(
  'className="alert error"',
  'className="message error"',
  'className="message success"',
  'className="state-card error-text"',
  'className="order-success',
  'setNotice',
  'const \[notice'
)

$failed = $false
foreach ($file in $files) {
  if (!(Test-Path $file)) {
    Write-Host "MISSING: $file" -ForegroundColor Red
    $failed = $true
    continue
  }

  foreach ($pattern in $patterns) {
    $matches = Select-String -Path $file -Pattern $pattern -ErrorAction SilentlyContinue
    if ($matches) {
      Write-Host "FOUND embedded notification pattern '$pattern' in $file" -ForegroundColor Red
      $matches | Select-Object Path, LineNumber, Line | Format-Table -AutoSize
      $failed = $true
    }
  }
}

if ($failed) {
  Write-Host "FAIL: Embedded dashboard notification UI still exists." -ForegroundColor Red
  exit 1
}

Write-Host "PASS: Product Dashboard and Admin Dashboard use Toast-only notification UI for success/error feedback." -ForegroundColor Green
