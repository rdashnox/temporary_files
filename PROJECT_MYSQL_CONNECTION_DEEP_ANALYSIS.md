# Project Deep Analysis and MySQL Connection Refused Fix

## Current error

The latest startup/migration failure is:

```text
WinError 10061 / Can't connect to MySQL server on '127.0.0.1'
```

This means the application reached the migration stage, but Windows refused the TCP connection to MySQL. The code is no longer failing because of Alembic, `.env` percent signs, or root access. The database URL is already synchronized to `finmark_app`, but the MySQL server itself is not reachable at the configured host/port.

## Most likely cause

MySQL Server is not running, or it is running on a different port than `3306`.

Common situations:

- MySQL80/MySQL84 service is stopped.
- XAMPP MySQL is not started.
- Laragon MySQL is not started.
- MySQL Workbench connects to another port such as `3307`.
- `.env` says `127.0.0.1:3306`, but Workbench uses a different MySQL connection.

## Project update practice

Do not keep extracting generated ZIP files over a running root folder. That mixes new code with old runtime files.

Before replacing the project folder, run:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
```

Then extract to a fresh folder or rename the old folder as backup.

## Fixes added

### New scripts

```text
diagnose-mysql-connection.ps1
repair-mysql-connection.ps1
scripts/mysql-connection-utils.ps1
MYSQL_CONNECTION_REFUSED_FIX.md
stop-frontend.ps1
```

### Updated scripts

```text
run-enterprise-migrations-mysql.ps1
seed-enterprise-mysql.ps1
start-microservices-local-mysql.ps1
verify-enterprise-mysql-databases.ps1
setup-enterprise-mysql.ps1
sync-enterprise-env-app-user.ps1
start-frontend.ps1
frontend/package.json
.env.example
README.md
```

## New recommended workflow

Run:

```powershell
.\diagnose-mysql-connection.ps1
```

If MySQL is stopped, try:

```powershell
.\repair-mysql-connection.ps1 -StartIfStopped
```

If MySQL Workbench uses port 3307, use:

```powershell
.\repair-mysql-connection.ps1 -HostName 127.0.0.1 -Port 3307 -StartIfStopped
```

Then run:

```powershell
.\setup-enterprise-mysql.ps1
.\run-enterprise-migrations-mysql.ps1
.\seed-enterprise-mysql.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

## What changed in frontend startup

The old Vite command used `--strictPort`, which crashes when port `5173` is already used. The new setup removes `--strictPort` and adds `start-frontend.ps1`, which searches for an available port from `5173` to `5185`.

## What changed in the ZIP package

The fixed ZIP excludes runtime artifacts:

```text
.venv
frontend/node_modules
.git
.pytest_cache
.microservices
logs
frontend/.env.local
.env
*.pyc
__pycache__
```

This reduces repeat errors caused by overwriting old runtime files.
