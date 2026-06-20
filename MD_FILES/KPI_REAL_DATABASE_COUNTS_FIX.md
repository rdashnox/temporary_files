# KPI Real Database Counts Fix

This refactor fixes the Admin Dashboard KPI cards for Users, Orders, Reports, and Audit Logs.

## Problem

The frontend previously calculated KPI values by calling each list API with `limit=1` and then using `data.length`.

Because only one row was requested, every KPI could only show `0` or `1` even when MySQL had more records.

## Fix

### Backend

Added a real summary endpoint:

```http
GET /api/v1/database/summary
```

It returns true database row counts using SQL `COUNT(*)` through SQLAlchemy:

```json
{
  "users": 8,
  "orders": 14,
  "reports": 6,
  "audit-logs": 42,
  "roles": 7,
  "permissions": 31,
  "planning-requests": 3
}
```

The endpoint respects the logged-in user's permissions. A user only receives counts for modules they can read.

### Frontend

Updated AdminDashboard to call:

```js
getDatabaseSummary()
```

instead of:

```js
listEntity(entity, { limit: 1 })
```

The KPI cards now show true MySQL row counts.

## Refresh behavior

KPI totals refresh:

1. When the Admin Dashboard first loads.
2. When the Refresh button is clicked.
3. After create, update, or delete actions.
4. Automatically every 30 seconds while the Admin Dashboard is open.

This avoids the old request loop while still keeping the numbers updated.

## Files changed

```text
backend/routes/database_entities.py
backend/services/database_entity_service.py
frontend/src/api/client.js
frontend/src/pages/AdminDashboard.jsx
```

## Validation

```text
Backend tests: 17 passed
Frontend build: successful
```
