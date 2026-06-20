# Legacy Auth to Enterprise Auth DB Migration

This project now includes a safe migration path for copying users, roles,
permissions, role-permission links, and user-role links from the old monolith
database `finmark_db` into the dedicated enterprise Auth database
`finmark_auth_db`.

## Why this is needed

The enterprise microservice version does not use the old `finmark_db` for
authentication. Login, roles, and permissions are owned by the Auth Service
and stored in `finmark_auth_db`.

If your old users still exist only in `finmark_db.users`, they must be
migrated into:

- `finmark_auth_db.auth_users`
- `finmark_auth_db.auth_roles`
- `finmark_auth_db.auth_permissions`
- `finmark_auth_db.auth_user_roles`
- `finmark_auth_db.auth_role_permissions`

## Recommended command

Use a MySQL account that can read the old `finmark_db`. Usually this is root:

```powershell
.\migrate-legacy-auth-to-enterprise.ps1 -LegacyUser root -PromptForLegacyPassword
```

Or pass the password directly:

```powershell
.\migrate-legacy-auth-to-enterprise.ps1 -LegacyUser root -LegacyPassword "your-root-password"
```

## If you want to use finmark_app to read the old database

First run this SQL in MySQL Workbench as root/admin:

```text
grant-legacy-auth-read-workbench.sql
```

Then run:

```powershell
.\migrate-legacy-auth-to-enterprise.ps1 -UseFinmarkAppForLegacyRead
```

## What the migration does

- Copies legacy permissions by code.
- Copies legacy roles by name.
- Copies legacy users by username/email.
- Preserves old password hashes so existing users can still log in.
- Verifies imported users by default so they can log in immediately.
- Recreates role-permission and user-role assignments.
- Guarantees `admin@example.com` exists and has the `Administrator` role.
- Gives Administrator/Admin roles every permission, including Product Dashboard access.

## Admin access guarantee

After migration, admin users can access:

- Admin Dashboard
- Product Dashboard
- Users
- Roles
- Permissions
- Orders
- Inventory/Product modules
- Notifications
- Reports
- Planning Requests
- Audit Logs

Demo admin login is reset to:

```text
admin@example.com
Admin@12345
```

## Verify in MySQL Workbench

Run:

```text
verify-auth-migration-workbench.sql
```

## Correct startup after migration

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\migrate-legacy-auth-to-enterprise.ps1 -LegacyUser root -PromptForLegacyPassword
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

Do not start the enterprise project using:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Use the microservice launcher instead.
