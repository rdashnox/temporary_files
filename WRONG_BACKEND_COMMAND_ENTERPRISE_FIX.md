# Wrong Backend Command Fix for Enterprise Microservice Mode

## Problem

This command starts the legacy single FastAPI application:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

In the full enterprise microservice setup, the project uses four dedicated databases:

- `finmark_auth_db`
- `finmark_order_db`
- `finmark_inventory_db`
- `finmark_notification_db`

The legacy single app still uses the old `DB_NAME` value, commonly `finmark_db`. The least-privilege MySQL user `finmark_app` is intentionally granted access only to the four dedicated enterprise databases. Therefore, the old command can fail with:

```text
Access denied for user 'finmark_app'@'127.0.0.1' to database 'finmark_db'
```

## Correct Command

Use the enterprise local launcher:

```powershell
.\start-microservices-local-mysql.ps1
```

Then start the frontend:

```powershell
.\start-frontend.ps1
```

## Full Safe Startup Sequence

```powershell
.\stop-microservices-local.ps1
.\repair-enterprise-env.ps1
.\verify-enterprise-mysql-databases.ps1
.\seed-enterprise-mysql.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

## Code Fix Added

`backend/app_factory.py` now detects when the enterprise four-database mode is enabled and `backend.main:app` is started by mistake. Instead of crashing during startup, it returns a clear API response explaining the correct commands.

This prevents confusing MySQL errors during project demonstrations.
