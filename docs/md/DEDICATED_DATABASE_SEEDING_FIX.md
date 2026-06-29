# FinMark Dedicated Database Seeding Fix

## What this fixes

The four MySQL databases can be created and migrated successfully, but they may still be empty or using `root` in `.env`. This update adds a clear seed command and a `.env` synchronization script.

## Correct sequence

```powershell
.\sync-enterprise-env-app-user.ps1
.\run-enterprise-migrations-mysql.ps1
.\seed-enterprise-mysql.ps1
.\verify-enterprise-mysql-databases.ps1
.\start-microservices-local-mysql.ps1
```

## What gets seeded

| Database | Seeded Data |
|---|---|
| `finmark_auth_db` | admin user, roles, permissions |
| `finmark_inventory_db` | product catalog |
| `finmark_order_db` | deterministic demo order, order items, order outbox event |
| `finmark_notification_db` | startup notification, sample order notification, inbox event |

Demo login:

```text
admin@example.com / Admin@12345
```

## MySQL Workbench verification

Open `verify-seeded-enterprise-data-workbench.sql` in MySQL Workbench and run it.

Important tables to show:

```text
finmark_auth_db.auth_users
finmark_inventory_db.inventory_products
finmark_order_db.order_orders
finmark_order_db.order_items
finmark_notification_db.notification_messages
```

## About fallback ports

Messages like this are not fatal:

```text
Preferred port 8101 is not available. Using fallback port 18101.
```

It means another process is already using the preferred port. This package now improves cleanup of stale local Uvicorn processes. Run this before starting again:

```powershell
.\stop-microservices-local.ps1
.\start-microservices-local-mysql.ps1
```

If fallback ports are still used, the app still works. Use the printed gateway URL, usually:

```text
http://127.0.0.1:18000/api/v1
```


## Empty DATABASE_URL sync fix

If PowerShell reports that `DATABASE_URL` cannot be set to an empty string, use the updated package. The sync scripts now remove the legacy single-database `DATABASE_URL` line completely and keep only the four enterprise URLs:

```env
AUTH_DATABASE_URL=...finmark_auth_db
ORDER_DATABASE_URL=...finmark_order_db
INVENTORY_DATABASE_URL=...finmark_inventory_db
NOTIFICATION_DATABASE_URL=...finmark_notification_db
```

Run:

```powershell
.\sync-enterprise-env-app-user.ps1
.\seed-enterprise-mysql.ps1
```
