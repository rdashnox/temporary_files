# Admin Dashboard CRUD Module

This refactor adds a full database-backed admin module for FinMark.

## What was added

### Backend CRUD endpoints

All endpoints are under:

```text
/api/v1/database
```

Available modules:

```text
/users
/roles
/permissions
/orders
/reports
/planning-requests
/audit-logs
```

Each module now supports these operations where appropriate:

```text
GET    /api/v1/database/{entity}
POST   /api/v1/database/{entity}
GET    /api/v1/database/{entity}/{id}
PUT    /api/v1/database/{entity}/{id}
DELETE /api/v1/database/{entity}/{id}
```

Examples:

```text
GET    /api/v1/database/users
POST   /api/v1/database/users
PUT    /api/v1/database/users/1
DELETE /api/v1/database/users/1
```

### Frontend CRUD dashboard

New React page:

```text
frontend/src/pages/AdminDashboard.jsx
```

It includes admin screens for:

```text
Users
Roles
Permissions
Orders
Reports
Planning Requests
Audit Logs
```

Features:

```text
- Sidebar module navigation
- Search per module
- Create/edit forms
- Delete/deactivate actions
- Role assignment for users
- Permission assignment for roles
- Status update controls for orders, reports, and planning requests
- Audit log viewing and manual audit entries
```

### API client helpers

Updated file:

```text
frontend/src/api/client.js
```

New helper functions:

```javascript
getCurrentDatabaseUser()
listEntity(entity, params)
createEntity(entity, payload)
updateEntity(entity, id, payload)
deleteEntity(entity, id)
```

### Backend files changed

```text
backend/routes/database_entities.py
backend/schemas/database_entities.py
backend/services/database_entity_service.py
```

### Tests added

```text
backend/tests/test_admin_crud.py
```

Test result:

```text
15 passed
```

## How to run

Backend:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Then open:

```text
http://127.0.0.1:5173
```

## Demo admin login

```text
Email: user@example.com
Password: Password123!
```

## Notes

The `DELETE /users/{id}` operation deactivates the user instead of hard-deleting the row. This is safer because orders, reports, planning requests, and audit logs may still reference the user.

Audit logs are included in CRUD for school/demo completeness, but in a real production system audit logs should normally be append-only and not editable.
