# Admin Order Edit Internal Server Error Fix

## Symptom

`verify-admin-order-edit.ps1` creates a checkout order successfully, then fails here:

```text
PUT http://127.0.0.1:<gateway-port>/api/v1/orders/<id>
Internal Server Error
```

## Meaning

The checkout flow and Admin list read flow are already working. The failure is inside the Order Service update transaction.

## Fix

The Order Service now uses a MySQL-safe replacement strategy for order items. It bulk-deletes existing rows from `order_items`, flushes the delete, then inserts the edited rows. This avoids unique-key conflicts on `(order_id, product_id)` and stale SQLAlchemy relationship state.

## Required Restart

You must restart the microservices after extracting this ZIP:

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

Then test:

```powershell
.\verify-admin-order-edit.ps1
```
