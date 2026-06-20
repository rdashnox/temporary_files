# .env File Lock Fix

## Problem

Windows may show this error when starting local enterprise microservices:

```text
Set-Content : The process cannot access the file '.env' because it is being used by another process.
```

This means `.env` was temporarily locked by another process such as VS Code, Notepad, antivirus scanning, or a running backend process.

## What was fixed

`sync-enterprise-env-app-user.ps1` was updated to:

- update `.env` only once instead of many times;
- skip rewriting `.env` if the values are already correct;
- retry file writes when Windows temporarily locks `.env`;
- remove the legacy `DATABASE_URL` safely;
- give clearer recovery steps if the file remains locked.

## Recommended commands

```powershell
.\stop-microservices-local.ps1
.\sync-enterprise-env-app-user.ps1
.\seed-enterprise-mysql.ps1
.\start-microservices-local-mysql.ps1
```

If `.env` is still locked, close `.env` in VS Code/Notepad and close extra terminals running the backend.

## Manual workaround

If your `.env` is already correct and only the startup sync is blocked, you may start with:

```powershell
.\start-microservices-local-mysql.ps1 -SkipEnvSync
```

Use this only after confirming `.env` has these four URLs:

```env
AUTH_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_auth_db
ORDER_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_order_db
INVENTORY_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_inventory_db
NOTIFICATION_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_notification_db
```
