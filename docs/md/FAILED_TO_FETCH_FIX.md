# Login Failed to Fetch Fix

`Failed to fetch` means the React frontend cannot reach the FastAPI backend.

## Correct startup

Open Terminal 1 from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Check this opens:

```text
http://127.0.0.1:8000/docs
```

Open Terminal 2:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Frontend API setting

The React app now defaults to:

```text
http://127.0.0.1:8000/api/v1
```

You can override it by creating `frontend/.env.local`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Restart `npm run dev` after changing environment variables.
