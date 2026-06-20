# Backend README

This backend is a FastAPI API for the FinMark PlatformTech project. It handles authentication, role-based access, database CRUD modules, product checkout, and KPI summary counts.

## Backend Features

- FastAPI application in `backend/main.py`.
- SQLAlchemy database connection in `backend/database.py`.
- MySQL models in `backend/models.py`.
- JWT login and refresh token routes.
- Protected admin CRUD routes.
- Protected product and checkout routes.
- Database summary endpoint for real KPI totals.
- Demo data seeding support.
- Backend tests with Pytest.

## Important Routes

```text
GET  /api/v1/health
POST /api/v1/auth/token
POST /api/v1/auth/refresh
POST /api/v1/auth/register
GET  /api/v1/shop/products
POST /api/v1/shop/checkout
GET  /api/v1/database/summary
GET  /api/v1/database/users
GET  /api/v1/database/roles
GET  /api/v1/database/permissions
GET  /api/v1/database/orders
GET  /api/v1/database/reports
GET  /api/v1/database/planning-requests
GET  /api/v1/database/audit-logs
```

## Demo Accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `Admin123!` |
| Manager | `manager@example.com` | `Manager123!` |
| Staff | `staff@example.com` | `Staff123!` |
| Viewer | `viewer@example.com` | `Viewer123!` |
| Customer | `customer@example.com` | `Customer123!` |
| User | `user@example.com` | `Password123!` |

## Backend Setup

From the project root:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create `.env` from `.env.example` and update MySQL credentials:

```env
DB_DRIVER=mysql+pymysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=finmark_db
DB_USER=root
DB_PASSWORD=your_mysql_password
```

## Database Setup

Run these scripts in MySQL Workbench:

1. `backend/scripts/schema_and_seed_mysql.sql`
2. `backend/scripts/finmark_refactor_seed_no_values_safe.sql`

Then verify connection:

```powershell
python -m backend.scripts.check_database_connection
```

## Run Backend

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

## Run Tests

```powershell
pytest
```

## Backend Folder Guide

```text
backend/
├── main.py                     FastAPI app and router registration
├── database.py                 SQLAlchemy engine/session setup
├── models.py                   Database models
├── core/config.py              Environment configuration
├── core/security.py            Password hashing and JWT helpers
├── dependencies/auth.py        Current-user and permission dependencies
├── routes/auth.py              Login, refresh, register routes
├── routes/shop.py              Product and checkout routes
├── routes/database_entities.py Admin CRUD and summary routes
├── services/                   Business/database logic
├── schemas/                    Pydantic request/response schemas
├── scripts/                    SQL setup and seed scripts
└── tests/                      Backend tests
```

## Enterprise Scale Notes

The backend now includes production-oriented settings for high concurrency:

```env
AUTO_CREATE_DB=false
SEED_DEMO_DATA=false
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
THREADPOOL_TOKENS=100
PRODUCT_CACHE_MAX_AGE_SECONDS=60
```

New endpoints:

```text
GET /api/v1/health        Liveness check
GET /api/v1/ready         Database readiness check
GET /api/v1/scale/profile Non-sensitive scaling profile
```

For 1,000 active users, use MySQL/PostgreSQL, multiple API workers, and the included Locust load test. Do not use SQLite or `uvicorn --reload` for production traffic.
