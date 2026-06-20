# MySQL Startup Fix: `orders.idempotency_key`

## Error fixed

The backend failed during startup with:

```text
pymysql.err.OperationalError: (1054, "Unknown column 'orders.idempotency_key' in 'field list'")
```

## Cause

The 1,000-active-user upgrade added checkout idempotency so duplicate checkout requests do not create duplicate orders. The code correctly added a new SQLAlchemy model column:

```text
orders.idempotency_key
```

However, if you already had an existing MySQL database, SQLAlchemy `create_all()` did not modify the old `orders` table. It only creates missing tables; it does not add missing columns to existing tables.

## Fix applied

`backend/database.py` now runs a safe local-development schema compatibility upgrade after `create_all()`.

When `AUTO_CREATE_DB=true`, startup now checks whether the existing `orders` table has `idempotency_key`. If missing, it automatically runs:

```sql
ALTER TABLE orders ADD COLUMN idempotency_key VARCHAR(120) NULL;
CREATE UNIQUE INDEX ix_orders_idempotency_key ON orders (idempotency_key);
```

It also safely creates the scale-related indexes when missing:

```sql
CREATE INDEX ix_orders_status_created_at ON orders (status, created_at);
CREATE INDEX ix_orders_user_created_at ON orders (user_id, created_at);
CREATE INDEX ix_notifications_user_created_at ON notifications (user_id, created_at);
```

## What to do

Use the updated ZIP, then run the backend again:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

## Manual fallback

If your MySQL user does not have `ALTER` or `CREATE INDEX` permission, run this file manually in MySQL Workbench:

```text
backend/scripts/enterprise_scale_migration.sql
```

Then start the backend again.
