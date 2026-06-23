# Order Edit Focus + Notification Refactor

## Objective

This refactor improves the Admin Dashboard order-edit workflow after the order edit duplicate-key issue was fixed.

New behavior:

1. When the admin clicks **Edit** on an order row, the page automatically scrolls to and focuses the edit form.
2. After the admin saves an edited order, the UI shows an edit notification message.
3. The Order Service emits an `order.updated` integration event.
4. The Notification Service can process `order.updated` and create an in-app notification.
5. Local no-Docker mode sets `NOTIFICATION_SERVICE_URL` so the Order Service can send the event to the Notification Service immediately when RabbitMQ is disabled.

## Files Changed

### Frontend

- `frontend/src/pages/AdminDashboard.jsx`
  - Added edit-form focus behavior using `editPanelRef`.
  - Added sticky order-edit toast notification.
  - After updating an order, dispatches `finmark:order-updated` and shows a visible notification.

- `frontend/src/styles.css`
  - Added highlight style for the active edit panel.
  - Added sticky edit notification toast styles.

### Backend

- `backend/enterprise/services/order_enterprise_service.py`
  - Keeps the duplicate order-item edit fix.
  - Adds `order.updated` outbox event after a successful edit.
  - Adds a local/no-Docker direct Notification Service fallback through `NOTIFICATION_SERVICE_URL`.

- `backend/enterprise/services/notification_enterprise_service.py`
  - Processes `order.updated` events.
  - Creates an in-app notification with the updated order number, status, actor, and changed fields.

- `backend/enterprise/scripts/notification_consumer.py`
  - RabbitMQ consumer now binds to `order.updated`.

- `start-microservices-local.ps1`
  - Sets `NOTIFICATION_SERVICE_URL` to the local gateway URL so edit notifications work in no-Docker local mode.

- `docker-compose.microservices.yml`
  - Adds `NOTIFICATION_SERVICE_URL=http://microservice-gateway` for Docker/cloud mode.

- `verify-admin-order-edit.ps1`
  - Still verifies checkout and update.
  - Now also checks whether an order-edit notification is available.

## How to Run

After extracting the refactored ZIP into a clean folder, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1

.\stop-microservices-local.ps1
.\stop-frontend.ps1
.\start-microservices-local-mysql.ps1
.\start-frontend.ps1
```

Then test:

```powershell
.\verify-admin-order-edit.ps1
```

Expected result:

```text
PASS: Admin Order Edit successfully updated order ... to status SHIPPED.
PASS: Order edit notification is available: Order updated - ...
```

If the notification check says no persisted notification yet, restart the microservices once so the new `NOTIFICATION_SERVICE_URL` environment variable is applied.

## Browser Test

1. Login as admin.
2. Open Admin Dashboard.
3. Open Orders.
4. Click **Edit** on an order row.
5. The edit form should automatically scroll into view and focus.
6. Change the status or another field.
7. Click **Save changes**.
8. A sticky notification appears at the top of the Admin Dashboard.
