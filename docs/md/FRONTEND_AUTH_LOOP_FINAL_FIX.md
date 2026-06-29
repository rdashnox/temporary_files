# Frontend Auth Request Loop Final Fix

## Problem

When `npm run dev` was started, the FastAPI terminal appeared to loop with many repeated requests like:

```text
GET /api/v1/database/roles?limit=200 401 Unauthorized
GET /api/v1/database/permissions?limit=200 401 Unauthorized
GET /api/v1/database/users?limit=1 401 Unauthorized
```

The backend was not restarting. The React frontend was repeatedly calling protected admin endpoints with an invalid or missing token.

## Root cause

The admin dashboard was allowed to keep running after an unrecoverable `401 Unauthorized` response. In development, React effects and stale localStorage tokens could cause the dashboard to keep trying to load admin summary, roles, permissions, users, reports, orders, planning requests, and audit logs.

## Fixes applied

### 1. Added a real auth-expired error path

Updated:

```text
frontend/src/api/client.js
```

New behavior:

- If there is no access token and no refresh token, the request stops immediately.
- If refresh fails, tokens are cleared.
- A global `finmark:auth-expired` event is fired only once.
- Protected API calls no longer silently return `401` responses to dashboard loaders.

### 2. App now logs the user out on expired/invalid auth

Updated:

```text
frontend/src/App.jsx
```

New behavior:

- The app listens for `finmark:auth-expired`.
- It clears old tokens.
- It unmounts the dashboard and returns to the login screen.

### 3. Admin Dashboard stops loading after auth failure

Updated:

```text
frontend/src/pages/AdminDashboard.jsx
```

New behavior:

- Admin loaders stop after the first auth failure.
- Summary and lookup loaders are guarded so they do not repeatedly fire.
- The dashboard displays `Your session expired. Please log in again.` instead of causing request spam.

### 4. Removed React StrictMode in development entry

Updated:

```text
frontend/src/main.jsx
```

This prevents React development mode from intentionally double-running effects, which made debugging API request behavior noisy.

## Recommended browser cleanup after applying this fix

Open DevTools and clear old tokens once:

```text
Application → Local Storage → http://localhost:5173 → delete access_token and refresh_token
```

Then log in again.

## Correct startup

Backend terminal:

```powershell
cd "C:\Users\ca\Documents\CONRAD\MAPUA\MO-IT151 - Platform Technologies\PROJECT\PlatformTech-SD1-MS2"
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend terminal:

```powershell
cd "C:\Users\ca\Documents\CONRAD\MAPUA\MO-IT151 - Platform Technologies\PROJECT\PlatformTech-SD1-MS2\frontend"
npm run dev
```

## Verified

```text
Frontend build: successful
Backend tests: 17 passed
```
