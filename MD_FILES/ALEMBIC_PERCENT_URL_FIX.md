# Alembic Percent URL Fix

## Error

```text
ValueError: invalid interpolation syntax in 'mysql+pymysql://finmark_app:FinmarkApp%402026!@127.0.0.1:3306/finmark_auth_db'
```

## Cause

The app user password is:

```text
FinmarkApp@2026!
```

Inside a SQLAlchemy database URL, `@` must be URL-encoded as `%40`:

```text
FinmarkApp%402026!
```

Alembic stores `sqlalchemy.url` in Python `configparser`. In `configparser`, `%` is used for interpolation, so the raw `%40` value causes `invalid interpolation syntax`.

## Fix Added

The four Alembic `env.py` files now escape `%` before putting the URL into Alembic configuration:

```python
def _escape_configparser_percent(value: str) -> str:
    return value.replace("%", "%%")
```

Patched files:

```text
backend/enterprise/migrations/auth/env.py
backend/enterprise/migrations/order/env.py
backend/enterprise/migrations/inventory/env.py
backend/enterprise/migrations/notification/env.py
```

## Correct `.env` Values

Keep `%40` in the `.env` database URLs. Do not change it back to raw `@` inside the URL.

```env
AUTH_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026!@127.0.0.1:3306/finmark_auth_db
ORDER_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026!@127.0.0.1:3306/finmark_order_db
INVENTORY_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026!@127.0.0.1:3306/finmark_inventory_db
NOTIFICATION_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026!@127.0.0.1:3306/finmark_notification_db
```

## Run Again

```powershell
.\.venv\Scripts\python.exe -m backend.enterprise.scripts.run_enterprise_migrations
```

or:

```powershell
.\run-enterprise-migrations-mysql.ps1
```
