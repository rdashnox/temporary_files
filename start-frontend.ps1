param(
    [int]$PreferredPort = 5173,
    [int]$MaxPort = 5185
)

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\frontend"

function Test-FinMarkPortFree {
    param([int]$Port)
    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse('127.0.0.1'), $Port)
        $listener.Start()
        return $true
    }
    catch { return $false }
    finally { if ($listener) { $listener.Stop() } }
}

npm config set registry https://registry.npmjs.org/

if (!(Test-Path "node_modules")) {
    npm install
}

$selectedPort = $null
for ($port = $PreferredPort; $port -le $MaxPort; $port++) {
    if (Test-FinMarkPortFree -Port $port) { $selectedPort = $port; break }
}

if (-not $selectedPort) {
    Write-Host "No available frontend port from $PreferredPort to $MaxPort." -ForegroundColor Red
    Write-Host "Run .\stop-frontend.ps1 from the project root, then try again." -ForegroundColor Yellow
    exit 1
}

if ($selectedPort -ne $PreferredPort) {
    Write-Host "Port $PreferredPort is busy. Using frontend fallback port $selectedPort." -ForegroundColor Yellow
}
else {
    Write-Host "Starting frontend on http://127.0.0.1:$selectedPort" -ForegroundColor Cyan
}

npx vite --host 127.0.0.1 --port $selectedPort
