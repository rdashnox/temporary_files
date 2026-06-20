# Admin Order List shows no records after checkout

## Root cause

The checkout flow was already working. The verification script proved that a new
checkout order could be created and then found by the Admin Order List API when
searched by order number.

The real issue is usually old seeded rows in `finmark_order_db.order_orders` with
lowercase statuses such as:

- `paid`
- `completed`

The backend model originally expected uppercase enum names such as:

- `PAID`
- `COMPLETED`

Because the Admin Dashboard loads the unfiltered order list, one bad legacy row
can make `/api/v1/orders` fail or return no visible records. Searching only for a
newly checked-out order can still pass, which is why the verification script can
pass while the browser list still looks empty.

## Fix

Run:

```powershell
.\repair-order-statuses.ps1
.\stop-microservices-local.ps1
.\start-microservices-local-mysql.ps1
.\stop-frontend.ps1
.\start-frontend.ps1
```

Then open the browser and press `Ctrl + F5`.

## MySQL Workbench option

Open and execute:

```text
repair-order-statuses-workbench.sql
```

Then restart services.
