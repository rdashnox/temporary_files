# Checkout to Admin Order List live-sync fix

## Problem
Checkout can succeed in the Product Dashboard, but the Admin Dashboard Order List can still appear empty when:

1. the browser is using a stale frontend bundle or stale Vite API base URL;
2. `/api/v1/orders` returns no rows due to a gateway/route mismatch;
3. the old compatibility endpoint `/api/v1/database/orders` is used instead of the dedicated Order Service;
4. the Admin page is already open and does not reload after checkout.

## Fixes added

- Frontend order list now tries `/orders`, `/orders/`, `/database/orders`, and `/database/orders/`.
- Frontend adds a cache-buster to order list calls.
- Product checkout now broadcasts a `finmark:order-created` browser event.
- Admin Dashboard listens for that event, switches to the Orders tab, and reloads the order list.
- Admin Dashboard retries the last created order number if the first list call returns empty.
- Order Service exposes `/api/v1/orders/debug/summary` and `/api/v1/orders/latest`.
- Added `diagnose-admin-order-list.ps1`.
- Updated `verify-orders-workbench.sql`.

## Correct test

```powershell
.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
.\diagnose-admin-order-list.ps1
.\verify-checkout-admin-order-list.ps1
```

If the API shows rows but the UI does not, press Ctrl+F5 in the browser or restart Vite using `stop-frontend.ps1` then `start-frontend.ps1`.
