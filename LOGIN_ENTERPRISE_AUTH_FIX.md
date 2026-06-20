# Login Fix for Full Enterprise Microservices

## Problem

Valid credentials can appear to fail because the frontend logged in successfully, then immediately called the legacy endpoint:

```text
/api/v1/database/me
```

In the full enterprise microservice system, the Auth Service owns user identity and exposes:

```text
/api/v1/auth/me
```

Also, reused MySQL databases can contain an older admin password hash. In that case, seeding did not reset the existing admin password.

## Fixes Added

- Frontend now calls `/api/v1/auth/me` after login.
- `/api/v1/database/me` remains available as a compatibility endpoint through the Auth Service.
- The enterprise auth seeder now repairs the demo admin account so it is active, verified, assigned Administrator, and reset to the documented password.
- Added `repair-enterprise-admin-login.ps1`.

## Commands

```powershell
.\repair-mysql-connection.ps1 -StartIfStopped
.\run-enterprise-migrations-mysql.ps1
.\repair-enterprise-admin-login.ps1
.\seed-enterprise-mysql.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

## Demo Login

```text
Email: admin@example.com
Password: Admin@12345
```

## Important

Do not use the old monolith command in enterprise mode:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Use:

```powershell
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```
