function Get-FinMarkDotEnvMap {
    param([string]$Path = (Join-Path $PSScriptRoot "..\.env"))

    $map = @{}
    if (!(Test-Path $Path)) { return $map }

    $lines = @(Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)
    foreach ($line in $lines) {
        if ($line -match '^\s*#') { continue }
        if ($line -match '^\s*$') { continue }
        $idx = $line.IndexOf('=')
        if ($idx -le 0) { continue }
        $key = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()
        $map[$key] = $value
    }
    return $map
}

function Get-FinMarkEnterpriseMySqlEndpoint {
    param([string]$EnvPath = (Join-Path $PSScriptRoot "..\.env"))

    $envMap = Get-FinMarkDotEnvMap -Path $EnvPath
    $url = $envMap['AUTH_DATABASE_URL']
    if ($url) {
        $match = [regex]::Match($url, '^[a-zA-Z0-9+.-]+://(?:[^@/]+@)?(?<host>[^:/?#]+)(?::(?<port>\d+))?')
        if ($match.Success) {
            $hostName = $match.Groups['host'].Value
            $portValue = $match.Groups['port'].Value
            if (-not $portValue) { $portValue = '3306' }
            return [pscustomobject]@{ HostName = $hostName; Port = [int]$portValue; Source = 'AUTH_DATABASE_URL' }
        }
    }

    $hostFromEnv = $envMap['DB_HOST']
    $portFromEnv = $envMap['DB_PORT']
    if (-not $hostFromEnv) { $hostFromEnv = '127.0.0.1' }
    if (-not $portFromEnv) { $portFromEnv = '3306' }
    return [pscustomobject]@{ HostName = $hostFromEnv; Port = [int]$portFromEnv; Source = 'DB_HOST/DB_PORT defaults' }
}

function Test-FinMarkTcpPort {
    param(
        [Parameter(Mandatory=$true)][string]$HostName,
        [Parameter(Mandatory=$true)][int]$Port,
        [int]$TimeoutMilliseconds = 2500
    )

    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $iar = $client.BeginConnect($HostName, $Port, $null, $null)
        $success = $iar.AsyncWaitHandle.WaitOne($TimeoutMilliseconds, $false)
        if (-not $success) { return $false }
        $client.EndConnect($iar)
        return $true
    }
    catch {
        return $false
    }
    finally {
        try { $client.Close() } catch {}
    }
}

function Get-FinMarkMySqlServices {
    try {
        return @(Get-Service -ErrorAction SilentlyContinue | Where-Object {
            $_.Name -match 'mysql|mariadb' -or $_.DisplayName -match 'MySQL|MariaDB'
        } | Sort-Object Status, Name)
    }
    catch {
        return @()
    }
}

function Start-FinMarkPossibleMySqlServices {
    $services = @(Get-FinMarkMySqlServices | Where-Object { $_.Status -ne 'Running' })
    foreach ($svc in $services) {
        try {
            Write-Host "Attempting to start MySQL-related service: $($svc.Name) ($($svc.DisplayName))" -ForegroundColor Cyan
            Start-Service -Name $svc.Name -ErrorAction Stop
        }
        catch {
            Write-Host "Could not start service $($svc.Name). You may need Administrator PowerShell or to start it from Services/XAMPP/Laragon." -ForegroundColor Yellow
        }
    }
}

function Show-FinMarkMySqlConnectionGuidance {
    param([string]$HostName, [int]$Port)

    Write-Host "" -ForegroundColor Red
    Write-Host "MySQL is not reachable at $($HostName):$Port." -ForegroundColor Red
    Write-Host "This is the cause of WinError 10061 / Connection refused." -ForegroundColor Yellow
    Write-Host "" 
    Write-Host "Fix options:" -ForegroundColor Cyan
    Write-Host "  1. Open Windows Services, start MySQL/MySQL80/MySQL84/MariaDB if it is stopped."
    Write-Host "  2. If you use XAMPP, open XAMPP Control Panel and start MySQL."
    Write-Host "  3. If you use Laragon, open Laragon and start MySQL."
    Write-Host "  4. In MySQL Workbench, confirm the connection host and port. Usually Hostname=127.0.0.1 and Port=3306."
    Write-Host "  5. If your MySQL uses a different port, run:"
    Write-Host "       .\repair-enterprise-env.ps1 -HostName 127.0.0.1 -Port YOUR_PORT"
    Write-Host "       .\setup-enterprise-mysql.ps1 -HostName 127.0.0.1 -Port YOUR_PORT"
    Write-Host "  6. To inspect port 3306 manually, run:"
    Write-Host "       netstat -ano | findstr :3306"
    Write-Host "" 
}
