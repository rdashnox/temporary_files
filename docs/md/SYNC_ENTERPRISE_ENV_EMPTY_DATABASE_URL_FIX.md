# Sync Enterprise Environment Empty DATABASE_URL Fix

## Problem

`sync-enterprise-env-app-user.ps1` failed with:

```text
Set-FinMarkDotEnvValue : Cannot bind argument to parameter 'Value' because it is an empty string.
```

The script was trying to clear the legacy single-database `DATABASE_URL` value. PowerShell rejected the empty string before the function could write the `.env` file.

## Fix

The scripts now remove the legacy `DATABASE_URL` entry instead of setting it to an empty value. The helper also accepts empty values safely for future use.

Updated scripts:

- `sync-enterprise-env-app-user.ps1`
- `setup-enterprise-mysql.ps1`
- `fix-mysql-root-access-denied.ps1`

## Correct workflow

```powershell
.\sync-enterprise-env-app-user.ps1
.\run-enterprise-migrations-mysql.ps1
.\seed-enterprise-mysql.ps1
.\verify-enterprise-mysql-databases.ps1
.\start-microservices-local-mysql.ps1
```

After running the sync script, verification should show URLs using `finmark_app`, not `root`.
