# Windows Locked Microservice Log File Fix

## Problem

When starting local enterprise microservices, Windows may show an error like:

```text
Remove-Item : Cannot remove item logs\microservices\auth-service-1.out.log because it is being used by another process.
```

This is not a database error. Your four dedicated MySQL databases may already be ready. The problem is only that Windows is holding an old log file open. This can happen when:

- an old Uvicorn process is still running;
- VS Code, Notepad, or PowerShell is viewing the log;
- antivirus/indexing temporarily scans the file.

## Fix added

`start-microservices-local.ps1` no longer deletes old log files before startup. It now creates unique log files for every run, for example:

```text
logs/microservices/auth-service-1-20260620-232500.out.log
logs/microservices/auth-service-1-20260620-232500.err.log
```

This prevents startup from crashing because of a locked old log file.

## Run commands

```powershell
.\stop-microservices-local.ps1
.\start-microservices-local-mysql.ps1
```

## Optional cleanup

To remove logs that are not locked:

```powershell
.\clear-microservice-logs.ps1
```

If a log is still locked, close VS Code/Notepad or restart PowerShell, then run the cleanup again.
