# Admin Order Edit Duplicate Item Final Fix

## Problem

The Admin Order Edit action failed with this MySQL error:

```text
Duplicate entry '<order_id>-<product_id>' for key 'order_items.uq_order_item_product'
```

The screenshot of `finmark_order_db.order_orders` confirms that parent orders are created correctly. The failure is in the child table `finmark_order_db.order_items`, where MySQL enforces one row per product inside each order using:

```text
UNIQUE(order_id, product_id)
```

## Root Cause

When the Admin edit form saves an order, it sends the full item list again. Older update logic attempted to delete all existing order items and insert replacements. In long-running local Uvicorn workers, SQLAlchemy/MySQL could still insert the replacement item before the old `(order_id, product_id)` row was fully cleared from session/database state, causing the duplicate-key failure.

## Final Fix

The order update service now synchronizes child order items in place:

1. Validate submitted items.
2. Detect duplicate product IDs in the submitted payload.
3. Load existing order items by `product_id`.
4. Update existing product rows instead of reinserting them.
5. Insert only new products.
6. Delete only products removed from the order.
7. Recalculate subtotal and total.
8. Expire relationship state so responses reload fresh rows.

This avoids duplicate inserts for unchanged products and keeps the unique key constraint intact.

## Files Updated

```text
backend/enterprise/services/order_enterprise_service.py
```

## How to Apply

After extracting this fixed ZIP:

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

If the same error still appears after extracting, old Uvicorn processes are still running an old copy of the code. Run:

```powershell
.\stop-microservices-local.ps1
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
.\start-microservices-local-mysql.ps1
```

Then run the verifier again.
