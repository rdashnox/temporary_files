# Backend Offline / Vite Proxy Error Fix

## Error fixed

The frontend log showed repeated Vite proxy errors like:

```text
Error: connect ECONNREFUSED 127.0.0.1:8000
[vite] http proxy error: /api/v1/database/roles?limit=200
```

This means the React/Vite frontend is running, but FastAPI is not available on:

```text
http://127.0.0.1:8000
```

The database may already be correct, but the backend server must also be running before the Admin Dashboard can load Users, Roles, Permissions, Orders, Reports, Planning Requests, and Audit Logs.

## What changed

- Added a frontend backend-health check before loading admin CRUD records.
- Added a visible Backend API offline banner in the Admin Dashboard.
- Prevented the Admin Dashboard from firing many database API requests when FastAPI is offline.
- Improved API client error messages with the exact backend start command.
- Kept the Product Dashboard, Admin Dashboard, Customer role, and CRUD modules unchanged.

## Correct startup order

Open Terminal 1 from the project root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m backend.scripts.check_database_connection
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Confirm this opens successfully:

```text
http://127.0.0.1:8000/api/v1/health
```

Open Terminal 2:

```powershell
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:5173
```

## Important

Keep the backend terminal open while using the frontend. If you close the backend terminal, Vite will show `ECONNREFUSED 127.0.0.1:8000` again because there is no server to forward API requests to.
