# MySQL Connection Refused Fix for FinMark Enterprise Microservices

## What the error means

The migration failed with:

```text
WinError 10061 / Can't connect to MySQL server on '127.0.0.1'
```

This means the backend is already using the correct enterprise database user, but no MySQL server is accepting TCP connections at the configured host and port.

Most common causes:

1. MySQL Server is stopped.
2. XAMPP or Laragon MySQL is not running.
3. MySQL is using a different port, such as `3307`.
4. The project `.env` points to `127.0.0.1:3306`, but Workbench connects to a different MySQL instance.
5. Firewall/security software is blocking local TCP MySQL.

## New diagnostic command

Run:

```powershell
.\diagnose-mysql-connection.ps1
```

To try starting a local MySQL/MariaDB Windows service automatically:

```powershell
.\diagnose-mysql-connection.ps1 -StartIfStopped
```

## Repair command

If your MySQL uses the normal port:

```powershell
.\repair-mysql-connection.ps1 -StartIfStopped
```

If your MySQL uses another port, for example `3307`:

```powershell
.\repair-mysql-connection.ps1 -HostName 127.0.0.1 -Port 3307 -StartIfStopped
```

Then run:

```powershell
.\setup-enterprise-mysql.ps1
.\run-enterprise-migrations-mysql.ps1
.\seed-enterprise-mysql.ps1
.\start-microservices-local-mysql.ps1
```

## Important Workbench check

In MySQL Workbench, open your connection settings and check:

- Hostname
- Port
- Username

Your project `.env` must use the same Hostname and Port.

## Clean update rule

Do not extract a new ZIP over a running project folder. Stop services first:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
```

Then extract to a fresh folder or clean runtime artifacts.
