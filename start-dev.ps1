$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

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

Import-FinMarkDotEnvFile -Path (Join-Path $projectRoot ".env")
$enterpriseEnabled = [System.Environment]::GetEnvironmentVariable("ENTERPRISE_MICROSERVICES_ENABLED", "Process")
$hasEnterpriseUrls = [System.Environment]::GetEnvironmentVariable("AUTH_DATABASE_URL", "Process") -and `
  [System.Environment]::GetEnvironmentVariable("ORDER_DATABASE_URL", "Process") -and `
  [System.Environment]::GetEnvironmentVariable("INVENTORY_DATABASE_URL", "Process") -and `
  [System.Environment]::GetEnvironmentVariable("NOTIFICATION_DATABASE_URL", "Process")

if ($enterpriseEnabled -and $enterpriseEnabled.ToLower() -eq "true" -and $hasEnterpriseUrls) {
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$projectRoot\start-microservices-local-mysql.ps1`""
} else {
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$projectRoot\start-backend.ps1`"", "-Legacy"
}
Start-Sleep -Seconds 4
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$projectRoot\start-frontend.ps1`""

Write-Host "Opened backend/microservices and frontend terminals."
Write-Host "Frontend: http://127.0.0.1:5173"
