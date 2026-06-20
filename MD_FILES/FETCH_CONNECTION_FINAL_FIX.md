# Final fix for Login failed: Cannot connect to the backend API

The React app now uses a Vite dev proxy:

- React calls: `/api/v1/auth/token`
- Vite forwards to: `http://127.0.0.1:8000/api/v1/auth/token`

This avoids browser CORS and `localhost` versus `127.0.0.1` issues.

## Recommended run method on Windows

From the project root, right-click PowerShell and run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-dev.ps1
```

This opens two terminals:

1. FastAPI backend on `http://127.0.0.1:8000`
2. React frontend on `http://127.0.0.1:5173`

## Manual run method

Terminal 1, project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open this to confirm the backend is alive:

```text
http://127.0.0.1:8000/api/v1/health
```

Terminal 2:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Demo login

```text
Email: user@example.com
Password: Password123!
```

## Important

Do not open the React app by double-clicking `index.html`.
Do not use Live Server for the React version.
Use `npm run dev`.
