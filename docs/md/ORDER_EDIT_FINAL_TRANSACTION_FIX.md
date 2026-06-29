# Admin Order Edit Final Transaction Fix

## Issue

Checkout works and the new order appears in the Admin Order List, but editing the order through:

```text
PUT /api/v1/orders/{id}
```

still returns **Internal Server Error**.

## Root Cause

The Order Service was receiving the edit request, but the update operation was too dependent on SQLAlchemy relationship state while replacing `order_items` rows.

The Admin form sends the full item list during edit, even when the user only changes the order status. That means the backend was unnecessarily deleting and reinserting the same `order_items` rows. On MySQL/local long-running service processes, this can leave stale child relationship state in the session and produce a generic 500 error.

## Fixes Applied

### 1. Update operation no longer eagerly loads child items

The update path now loads only the parent order row using `noload(OrderEntity.items)`. This prevents stale relationship data before child replacement.

### 2. No-op item updates are skipped

If the submitted item list is the same as the currently stored item list, the service now skips delete/reinsert and simply updates order fields such as status, customer name, delivery address, payment method, discount, shipping fee, and tax.

### 3. Child item replacement is safer

When item changes are real, the service:

```text
1. validates item rows
2. bulk-deletes old order_items using synchronize_session=False
3. flushes the delete
4. inserts clean replacement rows
5. recalculates subtotal and total
6. reloads a fresh order copy before returning
```

### 4. API errors are clearer

Unexpected update failures are now converted to a clear HTTP 400 JSON error message instead of a generic 500 Internal Server Error.

### 5. Verifier improved

`verify-admin-order-edit.ps1` now prints recent Order Service error logs if the update request fails.

## Files Updated

```text
backend/enterprise/services/order_enterprise_service.py
verify-admin-order-edit.ps1
ORDER_EDIT_FINAL_TRANSACTION_FIX.md
```

## How to Run

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
.\verify-admin-order-edit.ps1
```

Expected result:

```text
PASS: Admin Order Edit successfully updated order ... to status SHIPPED.
```

## Important

If the verifier still fails, check the new log output printed by `verify-admin-order-edit.ps1`. It will show the latest `order-service-*.err.log` lines so the exact MySQL or validation error can be seen immediately.
