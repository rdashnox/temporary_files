# FinMark PlatformTech SD1 MS2

FinMark is a full-stack **FastAPI + React + MySQL** dashboard project for platform technologies coursework. It includes authentication, role-based access control, an admin CRUD dashboard, a product dashboard, cart/checkout workflow, real database KPI counts, and MySQL seed scripts for repeatable local setup.

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, PyMySQL, JWT authentication
- **Frontend:** React 18, Vite, plain CSS dashboard UI
- **Database:** MySQL / MySQL Workbench
- **Testing:** Pytest for backend, Vite build for frontend
- **Local ports:** FastAPI `127.0.0.1:8000`, React/Vite `127.0.0.1:5173`

## Demo Accounts

Use these accounts after running the SQL setup and seed scripts.

| Role | Email | Password | Main Access |
|---|---|---|---|
| Admin | `admin@example.com` | `Admin123!` | Admin CRUD + Product Dashboard |
| Manager | `manager@example.com` | `Manager123!` | Operational admin access |
| Staff | `staff@example.com` | `Staff123!` | Product Dashboard + operational records |
| Viewer | `viewer@example.com` | `Viewer123!` | Read-only/product dashboard access |
| Customer | `customer@example.com` | `Customer123!` | Product Dashboard only |
| User | `user@example.com` | `Password123!` | Product Dashboard + checkout |

> `user@example.com / Password123!` is also seeded automatically by the Python development seeder. For the complete role demo, run the SQL seed scripts below.


## Microservice 3-Node Deployment

This version also includes a local/cloud-ready microservice deployment for the four core capabilities requested:

| Service | FastAPI entrypoint | Replicas/nodes | Gateway route |
|---|---|---:|---|
| Auth/Login | `backend.microservices.auth_main:app` | 3 | `/api/v1/auth`, `/api/v1/data`, `/api/v1/database` |
| Order | `backend.microservices.order_main:app` | 3 | `/api/v1/orders`, `/api/v1/shop` |
| Inventory | `backend.microservices.inventory_main:app` | 3 | `/api/v1/inventory` |
| Notification | `backend.microservices.notification_main:app` | 3 | `/api/v1/notifications` |

Run it locally with Docker:

```powershell
.\start-microservices.ps1
```

Or manually:

```powershell
docker compose -f docker-compose.microservices.yml up --build -d
```

The Nginx API Gateway runs on:

```text
http://127.0.0.1:8000
```

If one node of a service fails, Nginx passively fails over to the remaining two nodes. See `MICROSERVICE_3_NODE_DEPLOYMENT.md` for the architecture, failover test, and Kubernetes notes.

## What the Project Has

- FastAPI backend with modular routes, services, schemas, dependencies, and database models.
- React + Vite frontend with login, routing, admin dashboard, and product dashboard.
- MySQL database integration using SQLAlchemy ORM.
- JWT access token and refresh token authentication.
- Protected API routes with bearer-token validation.
- Role-based access control for Admin, Manager, Staff, Viewer, Customer, and User.
- Product Dashboard for Admin, Staff, Viewer, Customer, and User roles.
- Admin CRUD Dashboard for administrative users.
- Users, Roles, Permissions, Orders, Reports, Planning Requests, and Audit Logs modules.
- Real KPI cards for Users, Orders, Reports, and Audit Logs using database counts.
- KPI refresh after create, update, and delete operations.
- Backend-offline UI message instead of white blank screen.
- Frontend auth-loop protection to stop repeated 401 request spam.
- Users tab white-screen fix.
- Roles tab visible content and safe role rendering.
- Permission creation validation to prevent `422 Unprocessable Content`.
- Customer role that can only open the Product Dashboard.
- MySQL Workbench-safe seed script without deprecated `VALUES(column)` update syntax.
- Startup helper scripts for Windows PowerShell.
- Backend test coverage for auth, shop, and admin CRUD flows.

## Main Features

### Authentication

- Login with email/password.
- Password hashing with bcrypt.
- JWT access token and refresh token.
- Refresh-token lock to prevent multiple simultaneous refresh calls.
- Automatic logout when tokens are invalid or expired.
- Email verification fields and reset-password flow support.

### Product Dashboard

- Product catalog cards.
- Product search and category filtering.
- Add-to-cart workflow.
- Cart quantity increment/decrement.
- Cart clearing.
- Checkout form.
- Coupon support: `SAVE10`.
- Shipping and tax calculation.
- Product dashboard access for Admin, Staff, Viewer, Customer, and User roles.

### Admin Dashboard

- Users CRUD.
- Roles CRUD.
- Permissions CRUD.
- Orders CRUD.
- Reports CRUD.
- Planning Requests CRUD.
- Audit Logs CRUD.
- Search, edit, delete/deactivate controls.
- Real database KPI totals.
- KPI auto-refresh and refresh after data changes.
- Product Dashboard switch button for allowed roles.

### Database

- MySQL schema for users, roles, permissions, user roles, role permissions, orders, order items, reports, planning requests, and audit logs.
- Seeded demo accounts.
- Seeded permissions and role mappings.
- Safe enum/status normalization for SQLAlchemy compatibility.
- MySQL Workbench safe-update friendly scripts.

## Project Structure

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── start-dev.ps1
├── start-backend.ps1
├── start-frontend.ps1
├── backend/
│   ├── README.md
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── core/
│   ├── routes/
│   ├── services/
│   ├── schemas/
│   ├── dependencies/
│   ├── constants/
│   ├── scripts/
│   │   ├── README.md
│   │   ├── schema_and_seed_mysql.sql
│   │   ├── finmark_refactor_seed_no_values_safe.sql
│   │   ├── create_mysql_database.sql
│   │   ├── fix_mysql_access_denied.sql
│   │   ├── role_permission_alignment.sql
│   │   └── roles_tab_customer_refactor.sql
│   └── tests/
└── frontend/
    ├── README.md
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
```

## New Developer Setup After Pulling from GitHub

Use these steps when a new user clones or pulls the updated repository.

### 1. Required Software

Install these first:

- Python 3.11 to 3.13 is recommended. Python 3.14 can work with the pinned SQLAlchemy version, but 3.11/3.12/3.13 is safer for class/demo use.
- Node.js 20 LTS or newer.
- MySQL Server 8.x.
- MySQL Workbench.
- Git.
- VS Code or another editor.

Check versions:

```powershell
python --version
node --version
npm --version
mysql --version
```

### 2. Clone or Pull the Repository

```powershell
git clone <your-github-repo-url>
cd PlatformTech-SD1-MS2
```

If the project is already cloned:

```powershell
git pull origin main
```

### 3. Create the Backend Environment

From the project root:

```powershell
python -m venv .venv
```

Activate it:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install Python dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Create the `.env` File

Copy `.env.example` to `.env`:

```powershell
copy .env.example .env
```

Open `.env` and update your MySQL password:

```env
DB_DRIVER=mysql+pymysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=finmark_db
DB_USER=root
DB_PASSWORD=your_mysql_password
```

Keep this for local Vite development:

```env
FRONTEND_BASE_URL=http://localhost:5173
```

### 5. Create and Seed the MySQL Database

Open **MySQL Workbench** and connect to local MySQL.

Run this first to create the database tables and base data:

```text
backend/scripts/schema_and_seed_mysql.sql
```

Then run this second to apply the latest refactor seed, complete demo roles/users, safe updates, and status normalization:

```text
backend/scripts/finmark_refactor_seed_no_values_safe.sql
```

Optional scripts only when needed:

- `backend/scripts/fix_mysql_access_denied.sql` — use if root access fails and you want a dedicated `finmark_app` MySQL user.
- `backend/scripts/role_permission_alignment.sql` — use if old permissions do not match the new granular permissions.
- `backend/scripts/roles_tab_customer_refactor.sql` — use if only adding Customer role changes to an older database.
- `backend/scripts/customer_role_product_only_seed.sql` — use if only adding the Customer product-only account.

### 6. Verify Database Connection

From the project root with `.venv` active:

```powershell
python -m backend.scripts.check_database_connection
```

Expected result:

```text
Database connection successful
```

### 7. Run the Backend

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

### 8. Install and Run the Frontend

Open another terminal:

```powershell
cd frontend
npm config set registry https://registry.npmjs.org/
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

### 9. Faster Windows Start Option

From the project root:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-dev.ps1
```

This opens separate backend and frontend terminals.

## Common Issues and Fixes

### `ModuleNotFoundError: No module named 'backend'`

You are not in the project root. Run backend commands from the folder that contains `backend`, `frontend`, and `requirements.txt`.

```powershell
cd "C:\Users\ca\Documents\CONRAD\MAPUA\MO-IT151 - Platform Technologies\PROJECT\PlatformTech-SD1-MS2"
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### `.\.venv\Scripts\Activate.ps1 is not recognized`

Create the virtual environment first:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### PowerShell blocks activation

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Frontend shows backend offline or proxy errors

Make sure FastAPI is running:

```text
http://127.0.0.1:8000/docs
```

Then restart the frontend.

### Backend terminal shows many `401 Unauthorized` logs

Clear old browser tokens and login again:

```text
DevTools → Application → Local Storage → http://localhost:5173
Delete access_token and refresh_token
```

### KPI cards show wrong totals

Use the latest backend route:

```text
GET /api/v1/database/summary
```

Then restart both backend and frontend.

### `POST /api/v1/database/permissions 422 Unprocessable Content`

The permission form must send these fields:

```text
code
name
module
```

Example permission code:

```text
orders.export
```

The updated frontend can auto-derive:

```text
Name: Orders Export
Module: orders
```

## Testing

Run backend tests:

```powershell
pytest
```

Run frontend build:

```powershell
cd frontend
npm run build
```

## Suggested Demo Flow for Presentation

Show these in order:

1. Login page.
2. Admin login using `admin@example.com / Admin123!`.
3. Admin Dashboard KPI cards showing real MySQL counts.
4. Users tab showing user records and role assignment.
5. Roles tab showing role cards and role permissions.
6. Permissions tab creating a sample permission like `orders.export`.
7. Orders tab showing order records.
8. Reports tab showing report records.
9. Audit Logs tab showing recorded system activity.
10. Product Dashboard switch from Admin.
11. Add product to cart and checkout.
12. Customer login using `customer@example.com / Customer123!`.
13. Show that Customer can access Product Dashboard only and not Admin CRUD.
14. Add or update one record, then show KPI counts refreshing.
15. Open FastAPI docs at `http://127.0.0.1:8000/docs` to show backend API.
16. Open MySQL Workbench and show seeded tables: `users`, `roles`, `permissions`, `orders`, `reports`, `audit_logs`.

## API Highlights

```text
POST /api/v1/auth/token
POST /api/v1/auth/refresh
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

## Notes

- Keep backend and frontend running in separate terminals.
- Keep `.env` private. Do not commit real passwords or production secrets.
- For local demo, use the seeded accounts listed above.
- For production, replace the `SECRET_KEY`, database credentials, and demo passwords.


## Latest startup fix

If you see `Unknown column 'orders.idempotency_key' in 'field list'`, use this updated version. The backend now auto-upgrades the local MySQL schema when `AUTO_CREATE_DB=true`. See `MYSQL_IDEMPOTENCY_SCHEMA_FIX.md` for details and manual SQL fallback.
