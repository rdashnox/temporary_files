# Frontend README

This frontend is a React + Vite dashboard for the FinMark PlatformTech project.

## Frontend Features

- React login page.
- Product Dashboard.
- Admin CRUD Dashboard.
- Product catalog with cart and checkout.
- Admin modules for Users, Roles, Permissions, Orders, Reports, Planning Requests, and Audit Logs.
- Role-based dashboard routing.
- Real KPI totals loaded from the backend summary endpoint.
- Auth-expired handling to stop repeated request loops.
- Backend-offline banner.
- Safer form validation for Users and Permissions.

## Demo Accounts

| Role | Email | Password | Expected View |
|---|---|---|---|
| Admin | `admin@example.com` | `Admin123!` | Admin CRUD + Product Dashboard |
| Manager | `manager@example.com` | `Manager123!` | Admin/operations view |
| Staff | `staff@example.com` | `Staff123!` | Product Dashboard + operational records |
| Viewer | `viewer@example.com` | `Viewer123!` | Product/read-only view |
| Customer | `customer@example.com` | `Customer123!` | Product Dashboard only |
| User | `user@example.com` | `Password123!` | Product Dashboard + checkout |

## Install Frontend Dependencies

From the project root:

```powershell
cd frontend
npm config set registry https://registry.npmjs.org/
npm install
```

## Run Frontend

Make sure the backend is already running on `http://127.0.0.1:8000`.

```powershell
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Build Frontend

```powershell
npm run build
```

## API Proxy

The frontend calls API paths like:

```text
/api/v1/auth/token
/api/v1/database/summary
/api/v1/shop/products
```

Vite proxies `/api` to:

```text
http://127.0.0.1:8000
```

This is configured in `frontend/vite.config.js`.

## Clearing Old Tokens

If you see repeated `401 Unauthorized` logs or stale login behavior, clear browser storage once:

```text
DevTools → Application → Local Storage → http://localhost:5173
Delete access_token and refresh_token
```

Then login again.

## Suggested Frontend Demo

1. Login as Admin.
2. Show KPI cards with real database counts.
3. Click Users tab and show role assignments.
4. Click Roles tab and show available roles.
5. Create a permission in Permissions tab.
6. Switch to Product Dashboard.
7. Add an item to cart and checkout.
8. Logout and login as Customer.
9. Show Customer only sees Product Dashboard.
