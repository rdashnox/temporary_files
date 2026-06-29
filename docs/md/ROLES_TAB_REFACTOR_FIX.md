# Roles Tab Refactor Fix

## Problem
The Roles tab could open with no visible records or inconsistent behavior because the project had two permission naming styles:

- Older backend/frontend checks: `roles.manage`, `permissions.manage`, `planning.read`, `audit.read`
- Newer SQL seed permissions: `roles.read`, `roles.create`, `roles.update`, `roles.delete`, `permissions.read`, etc.

When the logged-in user came from the newer SQL seed, the dashboard could fail permission checks for role/permission endpoints.

## Fix Applied

### Backend
- Added permission alias handling in `backend/dependencies/auth.py`.
- `roles.read` can now access the Roles list/detail endpoints.
- `roles.create/update/delete` are accepted as compatible with `roles.manage`.
- `permissions.read/create/update/delete` are supported.
- `planning_requests.*` and `audit_logs.*` are supported as aliases for older planning/audit permissions.

### Frontend
- Updated `AdminDashboard.jsx` so the Roles tab uses `roles.read` for visibility.
- Updated the Permissions tab to use `permissions.read`.
- Added permission alias support in both `AdminDashboard.jsx` and `utils/access.js`.
- Cleared stale search text when switching admin tabs.
- Added clearer empty-state messaging when a tab has no records.
- Fixed sidebar role display so role objects show as `Admin` instead of `[object Object]`.

### SQL Helper
Run this if your database was seeded before granular permissions existed:

```sql
backend/scripts/role_permission_alignment.sql
```

## Recommended Test

Login as:

```text
admin@example.com / Admin123!
```

Then open:

```text
http://localhost:5173/admin
```

Click **Roles**. You should now see role records such as Admin, Manager, Staff, Viewer, etc.

## Verification

Backend tests:

```text
16 passed
```

Frontend build:

```text
vite build successful
```
