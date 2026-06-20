# Order Debug Route 404 Fix

## Problem

`diagnose-admin-order-list.ps1` failed at the Order Service debug summary step with:

```text
Invoke-RestMethod : {"detail":"Not Found"}
```

The checkout/order-list issue was being diagnosed through:

```text
GET /api/v1/orders/debug/summary
```

but the currently running gateway/service version did not expose that debug route. This can happen when old Uvicorn microservice processes are still running after extracting a newer ZIP, or when a local gateway points to service processes from a previous build.

## Fix Applied

### Backend

Updated `backend/enterprise/routes/orders.py` to expose multiple diagnostic aliases:

```text
GET /api/v1/orders/debug/summary
GET /api/v1/orders/debug-summary
GET /api/v1/orders/summary/debug
```

Updated `backend/enterprise/routes/database_compat.py` to expose compatibility diagnostic aliases:

```text
GET /api/v1/database/orders/debug/summary
GET /api/v1/database/orders/debug-summary
```

All debug routes read from the dedicated Order database:

```text
finmark_order_db.order_orders
```

### Diagnostic Script

Updated `diagnose-admin-order-list.ps1` so the debug route is optional. If the debug endpoint is missing on the currently running services, the script continues to check the real Admin Order List APIs:

```text
GET /api/v1/orders
GET /api/v1/database/orders
```

This prevents the diagnostic from stopping too early.

## Required Restart

After extracting this fixed version, stop old microservice processes first:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
```

Then start fresh:

```powershell
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

Then run:

```powershell
.\diagnose-admin-order-list.ps1
.\verify-checkout-admin-order-list.ps1
```

## Important

If `diagnose-admin-order-list.ps1` still shows `Not Found` for the debug route, it almost always means old service processes are still running. Stop them and restart the local microservices.
