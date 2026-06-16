# MySQL Database Integration Upgrade

This upgrade converts the backend from demo in-memory authentication storage to a SQLAlchemy-backed database layer that can run on MySQL Workbench at `localhost:3306`.

## What Changed

### New database layer

Added:

```text
backend/database.py
backend/models.py
backend/routes/database_entities.py
backend/services/audit_service.py
backend/services/seed_service.py
backend/scripts/create_mysql_database.sql
backend/scripts/seed_database.py
```

The database engine is configured from `.env` using:

```text
DATABASE_URL=mysql+pymysql://root:your_mysql_password@127.0.0.1:3306/finmark_db
DATABASE_ECHO=false
SEED_DEMO_DATA=true
```

### New tables/models

The backend now defines real SQLAlchemy models for:

| Table | Purpose |
|---|---|
| `users` | Stores accounts, verified status, reset tokens, and bcrypt password hashes. |
| `roles` | Stores RBAC roles such as Admin, Manager, and Staff. |
| `permissions` | Stores permission codes such as `orders.read`, `reports.manage`, and `audit.read`. |
| `user_roles` | Many-to-many table connecting users and roles. |
| `role_permissions` | Many-to-many table connecting roles and permissions. |
| `orders` | Stores checkout order headers/totals. |
| `order_items` | Stores persisted checkout line items. |
| `reports` | Stores generated/queued report jobs. |
| `planning_requests` | Stores planning requests and approval workflow status. |
| `audit_logs` | Stores important security and business actions. |

### Auth moved from memory to database

Removed the old `_IN_MEMORY_USERS` authentication store.

Now these flows persist to the database:

- Register user
- Email verification token
- Login check
- Last login timestamp
- Forgot password token
- Reset password
- User roles and permissions

### Password hashing

Passwords are still hashed using:

```python
passlib[bcrypt]
```

The database stores only `hashed_password`, never plain text.

Example bcrypt hash format:

```text
$2b$12$...
```

### New protected database endpoints

Added:

```text
GET  /api/v1/database/me
GET  /api/v1/database/roles
GET  /api/v1/database/permissions
GET  /api/v1/database/orders
GET  /api/v1/database/reports
POST /api/v1/database/reports
GET  /api/v1/database/planning-requests
POST /api/v1/database/planning-requests
GET  /api/v1/database/audit-logs
```

These use the existing bearer token authentication.

### Checkout now persists orders

`POST /api/v1/shop/checkout` now saves the order to:

```text
orders
order_items
audit_logs
```

The existing React checkout response shape was kept compatible.

## MySQL Workbench Setup

Open MySQL Workbench and run:

```sql
CREATE DATABASE IF NOT EXISTS finmark_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Optional dedicated app user:

```sql
CREATE USER IF NOT EXISTS 'finmark_user'@'localhost' IDENTIFIED BY 'change_this_password';
GRANT ALL PRIVILEGES ON finmark_db.* TO 'finmark_user'@'localhost';
FLUSH PRIVILEGES;
```

Then set `.env`:

```text
DATABASE_URL=mysql+pymysql://root:your_mysql_password@127.0.0.1:3306/finmark_db
```

or, if using the dedicated user:

```text
DATABASE_URL=mysql+pymysql://finmark_user:change_this_password@127.0.0.1:3306/finmark_db
```

## Run Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

On first startup, the app creates tables automatically for local development and seeds:

```text
user@example.com / Password123!
```

## Manual Seed Command

```powershell
python -m backend.scripts.seed_database
```

## Test Result

Backend tests passed after the integration:

```text
13 passed
```

## Production Notes

For production, replace automatic `Base.metadata.create_all()` with Alembic migrations, rotate `SECRET_KEY`, use a dedicated low-privilege MySQL user, store refresh tokens for revocation/logout, and consider HttpOnly cookies instead of browser `localStorage`.
