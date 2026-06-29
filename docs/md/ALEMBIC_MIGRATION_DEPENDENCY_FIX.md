# Alembic Migration Dependency Fix

## Error

```text
ModuleNotFoundError: No module named 'alembic'
```

## Cause

The enterprise microservice upgrade added formal database migrations using Alembic, but the existing `.venv` was created before Alembic was added. The code is correct; the Python virtual environment simply needs the updated packages from `requirements.txt`.

## Immediate Fix

From the project root, run:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then run the migration command again.

For local/no-Docker testing:

```powershell
.\.venv\Scripts\python.exe -m backend.enterprise.scripts.run_enterprise_migrations --local
```

For production/MySQL mode:

```powershell
.\.venv\Scripts\python.exe -m backend.enterprise.scripts.run_enterprise_migrations
```

Production/MySQL mode requires these database URLs or matching `.env` settings:

```env
AUTH_DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/finmark_auth_db
ORDER_DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/finmark_order_db
INVENTORY_DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/finmark_inventory_db
NOTIFICATION_DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/finmark_notification_db
```

## New Helper Scripts Added

### Install dependencies only

```powershell
.\install-enterprise-deps.ps1
```

### Run local migrations safely

```powershell
.\run-enterprise-migrations.ps1
```

If no argument is supplied, the helper uses `--local` automatically for no-Docker development.

### Run production/MySQL migrations

```powershell
.\run-enterprise-migrations.ps1 --service all
```

Make sure your MySQL database URLs are configured first.

## Script Improvements

`backend/enterprise/scripts/run_enterprise_migrations.py` now:

- catches missing Alembic errors and prints clear fix commands;
- supports `--local` for local SQLite databases;
- supports `--service auth|order|inventory|notification|all`;
- supports `--revision head` or another Alembic revision;
- prints common fixes for database connection errors.

## Recommended Local Command Sequence

```powershell
.\install-enterprise-deps.ps1
.\run-enterprise-migrations.ps1
.\start-microservices-local.ps1
```
