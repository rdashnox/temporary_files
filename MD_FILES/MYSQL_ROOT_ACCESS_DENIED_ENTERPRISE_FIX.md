# Fix: MySQL Access Denied for root in Enterprise 4-Database Mode

## Error

```text
pymysql.err.OperationalError: (1045, "Access denied for user 'root'@'localhost' (using password: YES)")
```

## Meaning

The app started, but the login request failed because the running backend tried to connect to MySQL as `root`. In the full enterprise setup, the correct local mode is the microservice launcher, not the legacy single-app backend.

Use this command for the four dedicated databases:

```powershell
.\start-microservices-local-mysql.ps1
```

Do not use this command for the full enterprise 4-DB demo unless you intentionally want the old single-app backend:

```powershell
.\start-backend.ps1 -Legacy
```

## Fast Fix

Run:

```powershell
.\fix-mysql-root-access-denied.ps1
.\verify-enterprise-mysql-databases.ps1
.\start-microservices-local-mysql.ps1
```

If verification fails, run the database setup again:

```powershell
.\setup-enterprise-mysql.ps1
```

Enter your real MySQL root/admin password when asked. The setup script creates the four databases and the `finmark_app` user.

## What the `.env` should contain

```env
ENTERPRISE_MICROSERVICES_ENABLED=true
AUTO_CREATE_DB=false
SEED_DEMO_DATA=false
EVENT_BUS_ENABLED=false
OTEL_ENABLED=false

AUTH_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_auth_db
ORDER_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_order_db
INVENTORY_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_inventory_db
NOTIFICATION_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_notification_db
```

The `%40` means `@` and `%21` means `!`. Keep these encoded values in URLs.

## Why this happened

`start-backend.ps1` starts `backend.main:app`, which is the compatibility single-app backend. The enterprise 4-DB setup uses:

- `backend.microservices.auth_main:app`
- `backend.microservices.order_main:app`
- `backend.microservices.inventory_main:app`
- `backend.microservices.notification_main:app`
- `backend.local_gateway:app`

The updated scripts now detect enterprise mode and redirect `start-backend.ps1` to the correct microservice launcher unless `-Legacy` is passed.
