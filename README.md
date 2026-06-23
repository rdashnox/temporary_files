# FinMark PlatformTech SD1 MS2


## Login Fix / Demo Admin

If the frontend says login failed even when the credentials are correct, repair the seeded Auth DB admin account and restart the enterprise microservices:

```powershell
.\repair-mysql-connection.ps1 -StartIfStopped
.\run-enterprise-migrations-mysql.ps1
.\repair-enterprise-admin-login.ps1
.\seed-enterprise-mysql.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

Demo login:

```text
admin@example.com
Admin@12345
```

The frontend now uses `/api/v1/auth/me` after token login. `/api/v1/database/me` is kept as a compatibility endpoint.


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

---

## Full Enterprise Microservice Mode

This project now includes a full enterprise-style microservice setup with separate databases:

- Auth DB
- Order DB
- Inventory DB
- Notification DB

It also includes:

- RabbitMQ message queue
- service-to-service JWT authentication through `X-Service-Token`
- OpenTelemetry/Jaeger tracing hooks
- Alembic migration folders per service
- outbox pattern for reliable event publishing
- 3 service nodes/replicas per microservice

Read the full guide:

```text
ENTERPRISE_MICROSERVICES_FULL_REPORT.md
```

### Run with Docker

```powershell
.\start-microservices.ps1
```

### Run without Docker

```powershell
.\start-microservices-local.ps1
```

### Local demo admin account

```text
admin@example.com / Admin@12345
```

### Enterprise endpoints

```text
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/api/v1/ready
http://127.0.0.1:8000/api/v1/service-info
```

## Alembic Migration Dependency Fix

If you see this error:

```text
ModuleNotFoundError: No module named 'alembic'
```

Run this from the project root:

```powershell
.\install-enterprise-deps.ps1
```

Then run local enterprise migrations:

```powershell
.\run-enterprise-migrations.ps1
```

Or run the Python command directly after installing requirements:

```powershell
.\.venv\Scripts\python.exe -m backend.enterprise.scripts.run_enterprise_migrations --local
```

For production/MySQL migration mode, configure the four database URLs first and run without `--local`.

See `ALEMBIC_MIGRATION_DEPENDENCY_FIX.md` for details.

## Windows `[WinError 10013]` Socket Fix

If Windows blocks the gateway or service ports, run:

```powershell
.\stop-microservices-local.ps1
.\start-microservices-local.ps1
```

The local startup script now probes ports before starting Uvicorn. If `8000`, `8101`, `8201`, `8301`, or `8401` are blocked/reserved, it automatically uses safe fallback ports and writes the selected API URL to:

```text
frontend/.env.local
```

To diagnose blocked/reserved ports, run:

```powershell
.\diagnose-windows-ports.ps1
```

Then restart the frontend so Vite reads the updated `.env.local` file.

---

## Four Dedicated MySQL Databases for Enterprise Microservices

To show the enterprise database-per-service setup in MySQL Workbench, run:

```powershell
.\setup-enterprise-mysql.ps1
```

This creates:

```text
finmark_auth_db
finmark_order_db
finmark_inventory_db
finmark_notification_db
```

It also updates `.env`, runs Alembic migrations, and seeds demo data.

If `mysql.exe` is not available in PowerShell, open this file in MySQL Workbench and execute it manually:

```text
setup-4-dedicated-databases-workbench.sql
```

Then run:

```powershell
.\run-enterprise-migrations-mysql.ps1
.\verify-enterprise-mysql-databases.ps1
.\start-microservices-local-mysql.ps1
```

See the full guide:

```text
MYSQL_WORKBENCH_4_DATABASE_SETUP.md
```

## Alembic `%40` MySQL Password Fix

If migrations fail with `ValueError: invalid interpolation syntax` and your database URL contains `%40`, use this fixed version. The four enterprise Alembic `env.py` files now escape `%` before writing the URL into Alembic's ConfigParser.

Keep the `.env` database URLs with `%40` when the MySQL password contains `@`:

```env
AUTH_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026!@127.0.0.1:3306/finmark_auth_db
ORDER_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026!@127.0.0.1:3306/finmark_order_db
INVENTORY_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026!@127.0.0.1:3306/finmark_inventory_db
NOTIFICATION_DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp%402026!@127.0.0.1:3306/finmark_notification_db
```

Then run:

```powershell
.\run-enterprise-migrations-mysql.ps1
```

## MySQL `root` Access Denied in Enterprise 4-DB Mode

If login returns:

```text
Access denied for user 'root'@'localhost'
```

you are likely running the legacy single-app backend instead of the enterprise 4-database microservice launcher. Run:

```powershell
.\fix-mysql-root-access-denied.ps1
.\verify-enterprise-mysql-databases.ps1
.\start-microservices-local-mysql.ps1
```

See `MYSQL_ROOT_ACCESS_DENIED_ENTERPRISE_FIX.md` for details.


### Fix for empty DATABASE_URL sync error

If `sync-enterprise-env-app-user.ps1` reports that `DATABASE_URL` cannot be an empty string, use the updated scripts in this package. The legacy single-database `DATABASE_URL` is removed, and the app uses the four dedicated enterprise URLs instead.

Run:

```powershell
.\sync-enterprise-env-app-user.ps1
.\run-enterprise-migrations-mysql.ps1
.\seed-enterprise-mysql.ps1
.\verify-enterprise-mysql-databases.ps1
```

Verification should show `finmark_app:***`, not `root:***`, in the database URLs.


## Windows .env File Lock Fix

If you see:

```text
Set-Content : The process cannot access the file '.env' because it is being used by another process.
```

Run:

```powershell
.\stop-microservices-local.ps1
.\sync-enterprise-env-app-user.ps1
.\start-microservices-local-mysql.ps1
```

If `.env` is open in VS Code or Notepad, close it first. The sync script now retries and writes `.env` only once to avoid Windows file-lock issues.

If `.env` is already correct, you can bypass startup sync:

```powershell
.\start-microservices-local-mysql.ps1 -SkipEnvSync
```


## Windows locked microservice log fix

If startup reports that it cannot remove `logs\microservices\*.log`, use the latest launcher. It creates unique log files per run instead of deleting old locked files.

```powershell
.\stop-microservices-local.ps1
.\start-microservices-local-mysql.ps1
```

Optional cleanup:

```powershell
.\clear-microservice-logs.ps1
```


## Fix: .env blank or empty sync error

If you see:

```powershell
Get-FinMarkDotEnvNewLines : Cannot bind argument to parameter 'OriginalLines' because it is an empty string.
```

run:

```powershell
.\stop-microservices-local.ps1
.
epair-enterprise-env.ps1
.erify-enterprise-mysql-databases.ps1
.\seed-enterprise-mysql.ps1
.\start-microservices-local-mysql.ps1
```

If the four database URLs are already correct and you only want to start the services, run:

```powershell
.\start-microservices-local-mysql.ps1 -SkipEnvSync
```


## Latest MySQL Connection Refused Fix

If migration fails with `WinError 10061` or `Can't connect to MySQL server on 127.0.0.1`, the MySQL server is not reachable at the host/port in `.env`.

Run:

```powershell
.\diagnose-mysql-connection.ps1
```

Then repair/start MySQL:

```powershell
.\repair-mysql-connection.ps1 -StartIfStopped
```

If MySQL Workbench uses another port, repair the `.env` using that port:

```powershell
.\repair-mysql-connection.ps1 -HostName 127.0.0.1 -Port 3307 -StartIfStopped
```

After MySQL is reachable:

```powershell
.\setup-enterprise-mysql.ps1
.\run-enterprise-migrations-mysql.ps1
.\seed-enterprise-mysql.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

Do not extract new project ZIPs over a running project folder. Stop services first:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
```

## Important: Enterprise Microservice Startup Command

For the full enterprise 4-database microservice version, do **not** start the backend with:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

That command starts the older monolith compatibility app and may try to use the legacy `finmark_db` database. The least-privilege `finmark_app` user is designed for the four dedicated databases only.

Use this instead:

```powershell
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

If you accidentally run the old Uvicorn command, the project now shows a clear guard message instead of crashing with a MySQL access-denied traceback.

See `WRONG_BACKEND_COMMAND_ENTERPRISE_FIX.md` for details.


## Legacy Users/Roles Migration to Dedicated Auth DB

To copy users, roles, permissions, user-role links, and role-permission links from the old monolith database `finmark_db` into `finmark_auth_db`, run:

```powershell
.\migrate-legacy-auth-to-enterprise.ps1 -LegacyUser root -PromptForLegacyPassword
```

If `finmark_app` should be used to read the old database, first run `grant-legacy-auth-read-workbench.sql` in MySQL Workbench as root/admin, then run:

```powershell
.\migrate-legacy-auth-to-enterprise.ps1 -UseFinmarkAppForLegacyRead
```

The migration guarantees that `admin@example.com` has full Administrator permissions and can open both the Admin Dashboard and Product Dashboard.

Verify in MySQL Workbench with:

```text
verify-auth-migration-workbench.sql
```

## Manage Order List Fix

If checkout succeeds but the Admin Dashboard does not show the order, use this fixed build. The frontend now reads orders from the dedicated Order Service endpoint `/api/v1/orders`, and `/api/v1/database/orders` remains available as a compatibility route. See `ORDER_MANAGE_LIST_FIX.md`.


## Checkout to Admin Order List Verification

Start the enterprise MySQL microservices first:

```powershell
.\start-microservices-local-mysql.ps1
```

Then verify checkout-to-admin-order-list flow:

```powershell
.\verify-checkout-admin-order-list.ps1
```

If no gateway is running, the verifier can start it automatically:

```powershell
.\verify-checkout-admin-order-list.ps1 -StartIfDown
```

The verifier now auto-detects the gateway port from `.microservices`, `frontend\.env.local`, and common fallback ports.


## Order Debug Route 404 Fix

If `diagnose-admin-order-list.ps1` fails with `{"detail":"Not Found"}` at the Order Service debug summary step, stop old service processes and start the fixed local microservices again:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
.\diagnose-admin-order-list.ps1
```

The fixed diagnostic script now falls back to the real order-list endpoints even if a debug route is missing on an older running service. See `ORDER_DEBUG_ROUTE_FIX.md`.

## API base route

Opening the API base URL `/api/v1` now shows a gateway index with available microservice prefixes. Use `/api/v1/health`, `/api/v1/ready`, `/api/v1/service-info`, `/api/v1/auth`, `/api/v1/orders`, `/api/v1/inventory`, or `/api/v1/notifications` for actual API actions.

## Admin Order List shows no records after checkout

If `verify-checkout-admin-order-list.ps1` can create and search a new order, but the browser Admin Dashboard still says **No orders found**, repair old seeded order statuses:

```powershell
.\repair-order-statuses.ps1
.\stop-microservices-local.ps1
.\start-microservices-local-mysql.ps1
.\stop-frontend.ps1
.\start-frontend.ps1
```

Cause: older Workbench demo seed scripts inserted lowercase order statuses such as `paid` and `completed`. The Enterprise Order Service now normalizes status values, and `repair-order-statuses.ps1` updates existing rows in `finmark_order_db.order_orders`.

## Admin Order Edit Fix

If orders appear in Admin Dashboard but **Edit / Save changes** fails, run:

```powershell
.\verify-admin-order-edit.ps1
```

This verifies that the Order Service can update an order through the same route used by the Admin Dashboard. The fix prevents duplicate `(order_id, product_id)` failures when replacing order items during edit.


## Admin Order Edit Internal Server Error Fix

If order delete works but order edit fails with `Internal Server Error`, extract the latest fixed ZIP and restart all services:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
.\verify-admin-order-edit.ps1
```

This fix updates `backend/enterprise/services/order_enterprise_service.py` to replace order items using a MySQL-safe bulk delete + flush + insert sequence.

## Admin Order Edit Final Transaction Fix

If checkout and order listing work but Admin Order Edit returns `Internal Server Error`, use the latest transaction-safe update logic. The Order Service now skips no-op item replacement, loads the order parent row without stale child relationships, and returns clearer API errors if MySQL rejects an update.

Run:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
.\verify-admin-order-edit.ps1
```

See `ORDER_EDIT_FINAL_TRANSACTION_FIX.md` for details.

## Order Edit Focus + Notification Update

This build includes the final order-edit workflow improvement:

- Clicking **Edit** in Admin Dashboard → Orders now scrolls to and focuses the edit form.
- Saving an edited order shows a sticky edit notification in the Admin Dashboard.
- The Order Service emits an `order.updated` event.
- The Notification Service can create an in-app notification from that edit event.

Run this verifier after starting the services:

```powershell
.\verify-admin-order-edit.ps1
```

See `ORDER_EDIT_FOCUS_NOTIFICATION_REFACTOR.md` for details.

## Enterprise Validation and Missing-Input Handling

This build includes enterprise-grade validation for frontend forms and backend API endpoints. Missing/null/invalid values now return controlled 400/422-style responses with clear messages instead of causing application crashes.

Run the validation test after starting the local microservices:

```powershell
.\start-microservices-local-mysql.ps1
.\verify-invalid-input-handling.ps1
```

See `VALIDATION_ERROR_HANDLING_REPORT.md` for the full validation scope.
