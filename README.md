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

# FinMark Enterprise Microservices Terminal Commands

This file contains the complete PowerShell command sequence for testing the FinMark enterprise microservice system.

Use these commands from your project root:

```powershell
C:\Users\ca\Documents\CONRAD\MAPUA\MO-IT151 - Platform Technologies\PROJECT\PlatformTech-SD1-MS2
```

---

## 1. Allow PowerShell Scripts and Activate Virtual Environment

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

## 2. Stop Old Running Services First

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
```

Optional force-stop old Python and Node processes:

```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 3. Install Backend and Frontend Dependencies

```powershell
.\install-enterprise-deps.ps1
```

```powershell
cd frontend
npm install
cd ..
```

---

## 4. Check MySQL Connection

```powershell
.\diagnose-mysql-connection.ps1
```

If MySQL is stopped, run:

```powershell
.\repair-mysql-connection.ps1 -StartIfStopped
```

---

## 5. Repair and Sync Enterprise `.env`

```powershell
.\repair-enterprise-env.ps1
.\sync-enterprise-env-app-user.ps1
```

---

## 6. Verify the Four Dedicated Databases

```powershell
.\verify-enterprise-mysql-databases.ps1
```

Expected databases:

```text
finmark_auth_db
finmark_order_db
finmark_inventory_db
finmark_notification_db
```

---

## 7. Run Migrations and Seed Demo Data

```powershell
.\run-enterprise-migrations-mysql.ps1
.\seed-enterprise-mysql.ps1
```

Optional admin login repair:

```powershell
.\repair-enterprise-admin-login.ps1
```

---

## 8. Start the Microservices

```powershell
.\start-microservices-local-mysql.ps1
.\start-microservices-local.ps1
```

Wait until you see messages like:

```text
Started auth-service-1
Started order-service-1
Started inventory-service-1
Started notification-service-1
Started local-api-gateway
```

The active gateway is usually:

```text
http://127.0.0.1:18000/api/v1
```

---

## 9. Check if All Nodes Are Running by Ports

```powershell
8101,8102,8103,8201,8202,8203,8301,8302,8303,8401,8402,8403,18000 |
ForEach-Object {
    $test = Test-NetConnection 127.0.0.1 -Port $_ -WarningAction SilentlyContinue
    [PSCustomObject]@{
        Port = $_
        Running = $test.TcpTestSucceeded
    }
} | Format-Table -AutoSize
```

Expected result:

```text
8101 True   Auth node 1
8102 True   Auth node 2
8103 True   Auth node 3

8201 True   Order node 1
8202 True   Order node 2
8203 True   Order node 3

8301 True   Inventory node 1
8302 True   Inventory node 2
8303 True   Inventory node 3

8401 True   Notification node 1
8402 True   Notification node 2
8403 True   Notification node 3

18000 True  API Gateway
```

---

## 10. Show Microservice Nodes Clearly

```powershell
$nodes = @(
    @{Service="Auth"; Node="auth-service-1"; Port=8101},
    @{Service="Auth"; Node="auth-service-2"; Port=8102},
    @{Service="Auth"; Node="auth-service-3"; Port=8103},

    @{Service="Order"; Node="order-service-1"; Port=8201},
    @{Service="Order"; Node="order-service-2"; Port=8202},
    @{Service="Order"; Node="order-service-3"; Port=8203},

    @{Service="Inventory"; Node="inventory-service-1"; Port=8301},
    @{Service="Inventory"; Node="inventory-service-2"; Port=8302},
    @{Service="Inventory"; Node="inventory-service-3"; Port=8303},

    @{Service="Notification"; Node="notification-service-1"; Port=8401},
    @{Service="Notification"; Node="notification-service-2"; Port=8402},
    @{Service="Notification"; Node="notification-service-3"; Port=8403},

    @{Service="Gateway"; Node="local-api-gateway"; Port=18000}
)

$nodes | ForEach-Object {
    $test = Test-NetConnection 127.0.0.1 -Port $_.Port -WarningAction SilentlyContinue
    [PSCustomObject]@{
        Service = $_.Service
        Node    = $_.Node
        URL     = "http://127.0.0.1:$($_.Port)"
        Status  = if ($test.TcpTestSucceeded) { "RUNNING" } else { "STOPPED" }
    }
} | Format-Table -AutoSize
```

---

## 11. Test Gateway Health

```powershell
Invoke-RestMethod http://127.0.0.1:18000/api/v1/health
```

```powershell
Invoke-RestMethod http://127.0.0.1:18000/api/v1/ready
```

```powershell
Invoke-RestMethod http://127.0.0.1:18000/api/v1/service-info
```

---

## 12. Test Auth Login

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:18000/api/v1/auth/token" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "username=admin@example.com&password=Admin@12345"

$login
```

Save token:

```powershell
$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }
```

Test current user:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:18000/api/v1/auth/me" `
  -Headers $headers
```

---

## 13. Test Inventory Service

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:18000/api/v1/inventory/products" `
  -Headers $headers
```

---

## 14. Test Order List API

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:18000/api/v1/orders" `
  -Headers $headers
```

Compatibility route:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:18000/api/v1/database/orders" `
  -Headers $headers
```

---

## 15. Test Checkout to Admin Order List

```powershell
.\verify-checkout-admin-order-list.ps1
```

Expected result:

```text
PASS: Admin Manage Order List can read the newly checked-out order
```

---

## 16. Test Order Edit / Update

```powershell
.\verify-admin-order-edit.ps1
```

Expected result:

```text
PASS: Admin Order Edit successfully updated order
```

---

## 17. Test Admin Order List Diagnostic

```powershell
.\diagnose-admin-order-list.ps1
```

---

## 18. Test Notification Service

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:18000/api/v1/notifications" `
  -Headers $headers
```

---

## 19. Start Frontend

```powershell
.\start-frontend.ps1
```

Open the URL printed by Vite, usually:

```text
http://127.0.0.1:5173
```

If port `5173` is busy, the script should use another port.

---

## 20. Browser Test Flow

Login using:

```text
admin@example.com
Admin@12345
```

Then test:

```text
1. Product Dashboard
2. Add product to cart
3. Checkout
4. Admin Dashboard
5. Orders / Manage Order List
6. Click Refresh
7. Click Edit
8. Edit form should focus/scroll
9. Save edit
10. Notification should appear
```

If the browser still shows old data, press:

```text
Ctrl + F5
```

---

## 21. Stop Everything After Testing

```powershell
.\stop-frontend.ps1
.\stop-microservices-local.ps1
```

Optional force stop:

```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 22. Commands You Should Not Use Anymore

Do not run this for the enterprise microservice version:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Use this instead:

```powershell
.\start-microservices-local-mysql.ps1
```

The system now runs through:

```text
API Gateway
Auth Service x3
Order Service x3
Inventory Service x3
Notification Service x3
Four dedicated MySQL databases
```

---

## Quick Demo Command Set

Use this shorter set during project defense:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\verify-enterprise-mysql-databases.ps1
.\start-microservices-local-mysql.ps1
```

Check nodes:

```powershell
8101,8102,8103,8201,8202,8203,8301,8302,8303,8401,8402,8403,18000 |
ForEach-Object {
    $test = Test-NetConnection 127.0.0.1 -Port $_ -WarningAction SilentlyContinue
    [PSCustomObject]@{
        Port = $_
        Running = $test.TcpTestSucceeded
    }
} | Format-Table -AutoSize
```

Test APIs:

```powershell
Invoke-RestMethod http://127.0.0.1:18000/api/v1/health
Invoke-RestMethod http://127.0.0.1:18000/api/v1/service-info
.\verify-checkout-admin-order-list.ps1
.\verify-admin-order-edit.ps1
```

Start frontend:

```powershell
.\start-frontend.ps1
```

.\verify-invalid-input-handling.ps1