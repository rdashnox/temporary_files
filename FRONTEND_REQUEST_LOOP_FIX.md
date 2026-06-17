# Frontend Request Loop Fix

## Problem

When running `npm run dev`, the FastAPI terminal looked like it was looping because the React Admin Dashboard repeatedly called:

- `POST /api/v1/auth/refresh`
- `GET /api/v1/database/users?limit=1`
- `GET /api/v1/database/roles?limit=1`
- `GET /api/v1/database/permissions?limit=200`
- `GET /api/v1/database/orders?limit=1`
- `GET /api/v1/database/reports?limit=1`
- `GET /api/v1/database/planning-requests?limit=1`
- `GET /api/v1/database/audit-logs?limit=1`

The backend was not restarting by itself. It was receiving repeated requests from the frontend.

## Root Cause

`AdminDashboard.jsx` normalized the user object directly during render:

```jsx
const user = normalizeUser(rawUser);
```

That creates a new object every render. Because `visibleEntities`, `loadLookups`, and `loadSummary` depended on that object, the dashboard effects ran again after each state update. This caused repeated API calls.

At the same time, multiple simultaneous `401 Unauthorized` responses could each trigger their own `/auth/refresh` call.

## Fix Applied

### 1. Memoized the normalized user

```jsx
const user = useMemo(() => normalizeUser(rawUser), [rawUser]);
```

### 2. Added a stable permission signature

This keeps visible admin entities stable and prevents the dashboard from reloading every render.

### 3. Added single-flight token refresh

`client.js` now shares one `refreshPromise`, so several parallel 401 responses only trigger one refresh request.

## Result

The Admin Dashboard now loads once per relevant change instead of continuously calling the backend.

## Run Order

Backend terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend terminal:

```powershell
cd frontend
npm run dev
```

## Extra Tip

If the request loop still appears after applying this fix, clear old tokens from the browser:

1. Open DevTools
2. Go to Application
3. Open Local Storage
4. Delete `access_token` and `refresh_token`
5. Refresh and login again
