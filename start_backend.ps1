# Run from the project root in PowerShell.
# This starts the FastAPI backend on http://127.0.0.1:8000.

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
  . .\.venv\Scripts\Activate.ps1
}

python -m backend.scripts.check_database_connection
if ($LASTEXITCODE -ne 0) {
  Write-Host "Database connection failed. Check your .env DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, and DB_NAME." -ForegroundColor Red
  exit $LASTEXITCODE
}

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
