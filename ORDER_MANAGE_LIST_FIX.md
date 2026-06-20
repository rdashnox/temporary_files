# Manage Order List Fix

## Problem

New customer checkout orders were saved successfully through the enterprise Order Service endpoint:

```text
POST /api/v1/orders/checkout
```

However, the Admin Dashboard's **Manage Order List** still requested the old CRUD compatibility endpoint:

```text
GET /api/v1/database/orders
```

In the full enterprise microservice setup, orders are owned by the dedicated Order Service and stored in:

```text
finmark_order_db
```

Because the Admin Dashboard was not reading directly from the Order Service, newly checked-out orders could fail to appear in the Manage Order List.

## Fix Applied

### 1. Frontend Admin CRUD routing fixed

Updated:

```text
frontend/src/api/client.js
```

Order CRUD now routes to the Order Service:

```text
GET    /api/v1/orders
POST   /api/v1/orders
PUT    /api/v1/orders/{id}
DELETE /api/v1/orders/{id}
```

Other admin entities still use the compatibility API:

```text
/api/v1/database/users
/api/v1/database/roles
/api/v1/database/permissions
```

### 2. Backend compatibility endpoint added

Updated:

```text
backend/enterprise/routes/database_compat.py
```

Added compatibility routes for:

```text
/api/v1/database/orders
/api/v1/database/orders/{id}
```

These routes read/write from the dedicated Order DB, so older frontend calls or browser cache still work.

### 3. Admin offline guidance updated

Updated:

```text
frontend/src/pages/AdminDashboard.jsx
```

The Admin Dashboard no longer suggests the old monolith command. It now points to the enterprise startup scripts.

## After Updating

Restart both backend microservices and frontend:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

Then:

1. Login as admin.
2. Go to Product Dashboard.
3. Add product to cart.
4. Checkout.
5. Go to Admin Dashboard.
6. Open **Orders / Manage Order List**.
7. Click **Refresh** if the Orders tab was already open.

## MySQL Workbench Verification

Run this query in MySQL Workbench:

```sql
USE finmark_order_db;
SELECT id, order_number, customer_name, status, total, created_at
FROM order_orders
ORDER BY created_at DESC;
```

If the order appears in this table, it should now also appear in the Admin Dashboard Manage Order List.
