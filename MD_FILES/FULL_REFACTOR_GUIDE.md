# Full Project Refactor Guide

This refactor keeps the existing API behavior but organizes the backend into clearer layers so the project is easier to maintain, debug, and extend.

## What changed

### 1. Cleaner backend architecture

The backend is now organized by responsibility:

```text
backend/
  constants/
    products.py
  core/
    config.py
    security.py
  dependencies/
    auth.py
  routes/
    auth.py
    data.py
    database_entities.py
    shop.py
  schemas/
    auth.py
    database_entities.py
    shop.py
  services/
    auth_service.py
    audit_service.py
    database_entity_service.py
    seed_service.py
    shop_service.py
  database.py
  models.py
  main.py
```

### 2. Separated database environment variables

You can now configure MySQL using separate `.env` lines instead of one long `DATABASE_URL`.

```env
DB_DRIVER=mysql+pymysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=finmark_db
DB_USER=root
DB_PASSWORD=your_mysql_password
```

The app automatically builds the database URL internally.

You can still use `DATABASE_URL` if needed. If `DATABASE_URL` is present, it overrides the separated `DB_*` values.

### 3. Centralized security

Password hashing, password validation, and JWT token functions now live in:

```text
backend/core/security.py
```

This keeps authentication rules separate from user database logic.

### 4. Cleaner auth dependency

Bearer token validation and permission checks now live in:

```text
backend/dependencies/auth.py
```

This makes route files shorter and easier to understand.

### 5. Cleaner route files

Route files now mostly handle HTTP input/output only. Business logic was moved into services:

```text
backend/services/shop_service.py
backend/services/database_entity_service.py
```

### 6. Cleaner schemas

Pydantic request/response models are now grouped by feature:

```text
backend/schemas/auth.py
backend/schemas/shop.py
backend/schemas/database_entities.py
```

### 7. Improved MySQL debugging

Database startup errors now show a clearer message with the active database URL hidden safely without exposing the password.

Use this command to test the database connection:

```powershell
python -m backend.scripts.check_database_connection
```

## Recommended `.env`

Create `.env` in the project root:

```env
SECRET_KEY=my-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
EMAIL_TOKEN_EXPIRE_MINUTES=60
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=15
FRONTEND_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173
FRONTEND_BASE_URL=http://localhost:5173

DB_DRIVER=mysql+pymysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=finmark_db
DB_USER=root
DB_PASSWORD=your_mysql_password

DATABASE_ECHO=false
SEED_DEMO_DATA=true
```

## Run backend

```powershell
cd "C:\Users\ca\Documents\CONRAD\MAPUA\MO-IT151 - Platform Technologies\PROJECT\PlatformTech-SD1-MS2"
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt --upgrade
python -m backend.scripts.check_database_connection
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

## Run frontend

```powershell
cd frontend
npm install
npm run dev
```

## Test result

Backend automated tests passed after the refactor:

```text
13 passed
```

## Demo login

```text
Email: user@example.com
Password: Password123!
```
