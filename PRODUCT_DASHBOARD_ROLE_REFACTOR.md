# Product Dashboard Role Refactor

This refactor makes the Product Dashboard the default authenticated workspace and explicitly supports these roles:

- Admin
- Staff
- Viewer
- User

## Routes

After login, users are sent to the Product Dashboard by default.

```text
/products
/dashboard
```

Admin and Manager users can still open the Admin CRUD console:

```text
/admin
```

## Frontend changes

### Added

```text
frontend/src/pages/DashboardRouter.jsx
frontend/src/utils/access.js
```

### Updated

```text
frontend/src/App.jsx
frontend/src/pages/CartDashboard.jsx
frontend/src/pages/AdminDashboard.jsx
frontend/src/styles.css
```

## Behavior

### Admin

Admin users can open both:

```text
Product Dashboard
Admin CRUD Dashboard
```

After login, Admin users land on Product Dashboard first. They can click **Admin CRUD** to manage users, roles, permissions, orders, reports, planning requests, and audit logs.

### Staff, Viewer, User

Staff, Viewer, and User roles open the Product Dashboard directly.

They can browse products, add items to cart, and create persisted orders through the checkout flow.

### Direct URLs

```text
http://localhost:5173/products
http://localhost:5173/dashboard
http://localhost:5173/admin
```

If a non-admin user opens `/admin`, the app safely redirects them back to Product Dashboard.

## Test result

```text
Frontend build: passed
Backend tests: 15 passed
```
