# FinMark Project Update Deep Analysis and Clean Setup Guide

## Main Finding

Do **not** repeatedly extract a generated ZIP over the same root folder while the backend, frontend, or microservice processes are running.

That workflow can leave a mixed project state:

- old `.env` values mixed with new enterprise settings;
- stale `.microservices/local-pids.csv` files;
- locked `logs/microservices/*.log` files;
- old `frontend/node_modules` with new package scripts;
- old `.venv` dependencies mixed with new `requirements.txt`;
- old PowerShell scripts kept beside new scripts;
- running Uvicorn or Vite processes still holding ports and files.

This is why you saw repeated issues such as:

- `.env` cannot be written because it is locked;
- `.env` is read as blank or empty;
- `Write-FinMarkFileWithRetry` rejects empty generated lines;
- Vite reports `Port 5173 is already in use`;
- microservices fall back from port `8000` to `18000` or `18001`.

## Correct Update Method

Use this safer process when replacing the project with a new ZIP:

1. Stop all project processes:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
```

2. Backup the current folder:

```powershell
Rename-Item "PlatformTech-SD1-MS2" "PlatformTech-SD1-MS2-backup"
```

3. Extract the new ZIP into a fresh folder named:

```text
PlatformTech-SD1-MS2
```

4. Copy only your local configuration from the backup if needed:

```text
.env
frontend\.env.local
```

5. Do not copy these runtime folders from the old folder:

```text
.venv
frontend\node_modules
.microservices
.frontend
logs
.pytest_cache
__pycache__
```

6. Reinstall dependencies:

```powershell
.\install-enterprise-deps.ps1
cd frontend
npm install
cd ..
```

7. Repair enterprise `.env`, migrate, seed, verify, and start:

```powershell
.\repair-enterprise-env.ps1
.\run-enterprise-migrations-mysql.ps1
.\seed-enterprise-mysql.ps1
.\verify-enterprise-mysql-databases.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

## What Was Fixed in This Version

### 1. `.env` sync no longer fails when generated lines are empty

Updated:

```text
sync-enterprise-env-app-user.ps1
```

Fixes:

- accepts missing, blank, and empty `.env` content;
- rebuilds required enterprise database settings when generated content is empty;
- removes legacy `DATABASE_URL` and `DB_password` entries;
- writes `.env` with retry logic;
- keeps the four enterprise DB URLs using `finmark_app`, not `root`.

### 2. Frontend Vite port conflict fixed

Updated:

```text
frontend/package.json
start-frontend.ps1
```

Fixes:

- removed `--strictPort` from the Vite dev script;
- added frontend port fallback from `5173` to `5174` through `5185`;
- added a safer frontend starter.

### 3. Added frontend stop command

Added:

```text
stop-frontend.ps1
```

Purpose:

- stops stale Vite/node processes on common frontend ports;
- prevents `Port 5173 is already in use`.

### 4. Added runtime cleanup command

Added:

```text
clean-runtime-artifacts.ps1
```

Purpose:

- stops local microservices and frontend;
- removes stale local PID/log/cache folders;
- avoids locked files and stale process state.

## How to Show the Four Dedicated Databases in MySQL Workbench

Open MySQL Workbench and refresh **SCHEMAS**. You should see:

```text
finmark_auth_db
finmark_order_db
finmark_inventory_db
finmark_notification_db
```

Open these tables to prove the dedicated DB separation:

```text
finmark_auth_db.auth_users
finmark_inventory_db.inventory_products
finmark_order_db.order_orders
finmark_notification_db.notification_messages
```

## Recommended Daily Start Commands

After setup is already complete, use:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

If `.env` is already correct and Windows keeps locking it, use:

```powershell
.\start-microservices-local-mysql.ps1 -SkipEnvSync
.\start-frontend.ps1
```

## Notes About Fallback Ports

Fallback ports are not fatal. They only mean a preferred port was already used.

Example:

```text
8000 unavailable → gateway uses 18000 or 18001
5173 unavailable → frontend uses 5174 or higher
```

Always use the URL printed by the script.
