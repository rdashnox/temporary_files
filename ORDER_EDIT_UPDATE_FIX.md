# Admin Order Edit / Update Fix

## Problem

Delete works in the Admin Order List, but Edit/Save fails with an Internal Server Error during:

```powershell
PUT /api/v1/orders/{id}
```

The verifier showed that login, checkout, and order lookup already work, but update fails at the order update transaction.

## Root Cause

The Order Edit form sends the full order item list back to the API. The previous update logic used ORM relationship clearing while replacing items. On MySQL, this can produce a 500 error when the replacement list contains the same `product_id` as the existing row because the table has this uniqueness rule:

```sql
UNIQUE(order_id, product_id)
```

SQLAlchemy/MySQL may try to insert the replacement item while the old relationship row is still present or still tracked in the session.

## Fix Applied

The backend now replaces order items using a safer MySQL-friendly sequence:

1. Validate the edit payload.
2. Bulk delete old `order_items` by `order_id`.
3. Flush the delete operation.
4. Insert fresh replacement rows using explicit `order_id`.
5. Recalculate subtotal and total.
6. Expire/reload the order items relationship before returning the response.

Updated file:

```text
backend/enterprise/services/order_enterprise_service.py
```

## Commands

After extracting this fixed ZIP, restart all local services so the new Order Service code is loaded:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

Then run:

```powershell
.\verify-admin-order-edit.ps1
```

Expected result:

```text
PASS: Admin Order Edit successfully updated order ... to status SHIPPED.
```

If the script still fails, you are probably still running old Uvicorn processes. Run the stop command again, close any old PowerShell windows running Uvicorn, then start again.
