# .env Blank / Empty OriginalLines Sync Fix

## Error

```powershell
Get-FinMarkDotEnvNewLines : Cannot bind argument to parameter 'OriginalLines' because it is an empty string.
```

## Cause

PowerShell was reading `.env` as empty or blank, then the sync function rejected the empty value before it could rebuild the file.
This can happen if `.env` was newly created, accidentally cleared, or briefly locked by VS Code, antivirus, or a previous script.

## Fix added

`sync-enterprise-env-app-user.ps1` now accepts a missing, blank, or empty `.env` file and rebuilds the required enterprise MySQL settings.

It creates or repairs these values:

```env
ENTERPRISE_MICROSERVICES_ENABLED=true
AUTH_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_auth_db
ORDER_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_order_db
INVENTORY_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_inventory_db
NOTIFICATION_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026%21@127.0.0.1:3306/finmark_notification_db
```

## Recommended commands

```powershell
.\stop-microservices-local.ps1
.epair-enterprise-env.ps1
.erify-enterprise-mysql-databases.ps1
.\seed-enterprise-mysql.ps1
.\start-microservices-local-mysql.ps1
```

If `.env` is already correct and you only want to start services, use:

```powershell
.\start-microservices-local-mysql.ps1 -SkipEnvSync
```
