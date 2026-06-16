# MySQL 1045 Access Denied Fix

Your backend error:

```text
pymysql.err.OperationalError: (1045, "Access denied for user 'root'@'localhost' (using password: YES)")
```

This means the FastAPI backend reached MySQL, but MySQL rejected the username/password in `DATABASE_URL`.

## Recommended fix

Do not use `root` in your app `.env`. Create a local application user instead.

### 1. Open MySQL Workbench

Connect using the MySQL account that works in your Workbench.

### 2. Run this script

Open and run:

```text
backend/scripts/fix_mysql_access_denied.sql
```

It creates:

```text
Database: finmark_db
User: finmark_app
Password: FinmarkApp123
```

### 3. Edit your project-level `.env`

Your `.env` must be in the project root, same level as `backend` and `frontend`:

```text
PlatformTech-SD1-MS2/.env
```

Use this exact database URL:

```env
DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp123@127.0.0.1:3306/finmark_db
```

Full local example:

```env
SECRET_KEY=my-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
EMAIL_TOKEN_EXPIRE_MINUTES=60
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=15
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FRONTEND_BASE_URL=http://localhost:5173
DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp123@127.0.0.1:3306/finmark_db
DATABASE_ECHO=false
SEED_DEMO_DATA=true
```

### 4. Test the database connection

From project root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m backend.scripts.check_database_connection
```

Expected result:

```text
Database connection successful.
```

### 5. Start the backend

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

## If you still want to use root

Make sure the password in `.env` is exactly the same password that works in MySQL Workbench:

```env
DATABASE_URL=mysql+pymysql://root:YOUR_REAL_MYSQL_PASSWORD@127.0.0.1:3306/finmark_db
```

If your password contains special URL characters, encode them:

```text
@  becomes  %40
#  becomes  %23
:  becomes  %3A
/  becomes  %2F
```

Example:

```text
Password: pa@ss123
Encoded:  pa%40ss123
```

```env
DATABASE_URL=mysql+pymysql://root:pa%40ss123@127.0.0.1:3306/finmark_db
```
