# PlatformTech-SD1-MS2 — Service-Oriented Refactor Report

## Corrected objective
Act as a software developer with 20 years of experience in software development. Perform a deep analysis of the project, decouple the code into a Service-Oriented Architecture, focus on the core functionalities of login, order, inventory, and notification, remove the redundant **Add** button in the order/product card because **Add Cart** already performs the same action, and provide improvement recommendations.

## Executive analysis

The project is a FastAPI backend with a React/Vite frontend. The current backend already has a partial layered approach with `routes`, `schemas`, `models`, and `services`, but the previous `shop_service.py` was doing too much at once:

- product catalog retrieval
- stock validation
- checkout item preparation
- pricing calculation
- order persistence
- audit logging

This created tight coupling between product/inventory behavior and order checkout behavior. It also made future features like notification, payment retries, order tracking, and inventory reservation harder to add safely.

The refactor keeps all existing behavior working while introducing clear service boundaries for the requested core modules.

## Service-oriented changes applied

### 1. Login / Authentication Service
Existing authentication service remains the owner of:

- login validation
- registration
- email verification token generation
- password reset
- access/refresh token creation
- current user resolution

Main files:

- `backend/services/auth_service.py`
- `backend/controllers/auth_controller.py`
- `backend/routes/auth.py`

Recommended next step: add account lockout, login throttling, and real email delivery for verification/reset links.

### 2. Inventory Service
Added a dedicated inventory service:

- `backend/services/inventory_service.py`
- `backend/routes/inventory.py`

New endpoints:

- `GET /api/v1/inventory/products`
- `GET /api/v1/inventory/products/{product_id}`
- `GET /api/v1/inventory/stock/summary`

Responsibilities:

- list products
- search/filter products
- validate product existence
- validate available stock
- expose low-stock summary

### 3. Order Service
Added a dedicated order service:

- `backend/services/order_service.py`
- `backend/routes/orders.py`

New endpoints:

- `POST /api/v1/orders/checkout`
- `GET /api/v1/orders`
- `POST /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `PUT /api/v1/orders/{order_id}`
- `DELETE /api/v1/orders/{order_id}`

Responsibilities:

- checkout orchestration
- order CRUD
- order total recalculation
- order item replacement
- audit logging for order actions
- notification creation after order creation

The admin database route now delegates order work to `order_service.py` instead of keeping that concern inside the general database entity service.

### 4. Pricing Service
Added a pricing service:

- `backend/services/pricing_service.py`

Responsibilities:

- calculate subtotal
- calculate coupon discount
- calculate shipping fee
- calculate VAT/tax
- calculate total

This removes pricing rules from the route and checkout orchestration logic.

### 5. Notification Service
Added notification persistence and routes:

- `backend/services/notification_service.py`
- `backend/schemas/notification.py`
- `backend/routes/notifications.py`
- `Notification` model in `backend/models.py`

New endpoints:

- `GET /api/v1/notifications`
- `PATCH /api/v1/notifications/{notification_id}/read`
- `POST /api/v1/notifications/mark-all-read`

Responsibilities:

- create in-app notifications
- create order-created notifications
- create low-stock notification events
- list user/global notifications
- mark notifications as read

### 6. Legacy shop compatibility
The original endpoints remain available:

- `GET /api/v1/shop/products`
- `POST /api/v1/shop/checkout`

But they now act as a compatibility facade and delegate to:

- `inventory_service.py`
- `order_service.py`

This prevents breaking existing clients while allowing the frontend and future modules to use the cleaner SOA endpoints.

### 7. Frontend cleanup
Updated React frontend API calls:

- products now call `/api/v1/inventory/products`
- checkout now calls `/api/v1/orders/checkout`
- added `getNotifications()` client helper

Removed the redundant **Add** button from `ProductCard.jsx`; only **Add Cart** remains as the product-add action.

## High-level architecture after refactor

```text
React Frontend
   |
   |-- Auth API ----------------> Auth Service
   |-- Inventory API -----------> Inventory Service
   |-- Orders API --------------> Order Service
   |                               |-- Inventory Service
   |                               |-- Pricing Service
   |                               |-- Notification Service
   |                               |-- Audit Service
   |
   |-- Notifications API -------> Notification Service
   |
FastAPI Routes
   |
SQLAlchemy Models / Database
```

## Key improvement recommendations

### Priority 1 — Production readiness
1. Replace `Base.metadata.create_all()` with Alembic migrations.
2. Move secrets out of `.env` and use environment variables or a secret manager.
3. Add proper email provider integration for verification and password reset.
4. Add login rate limiting, account lockout, and MFA/2FA.
5. Add structured logging with request IDs.

### Priority 2 — Better domain design
1. Replace static product constants with a real `Product` / `InventoryItem` database table.
2. Add stock reservation during checkout to prevent overselling.
3. Add idempotency keys for checkout to avoid duplicate orders on retry.
4. Add order status transition rules, for example `NEW -> PAID -> PACKED -> SHIPPED`.
5. Add notification templates and channels: in-app, email, SMS, webhook.

### Priority 3 — Frontend and UX
1. Connect the notification bell to the new notification API.
2. Add loading/success/error states for notification actions.
3. Show stock warning badges directly from `/inventory/stock/summary`.
4. Add order detail view and order timeline.
5. Add role-aware navigation so users only see modules they can access.

### Priority 4 — Testing and maintainability
1. Add service-level unit tests for inventory, pricing, order, and notification services.
2. Add API tests for the new `/inventory`, `/orders`, and `/notifications` routes.
3. Add frontend component tests for cart/order behavior.
4. Add CI pipeline that runs backend tests and frontend build automatically.
5. Add OpenAPI route descriptions and examples for Swagger UI.

## Validation performed

Backend tests passed:

```text
17 passed
```

Frontend production build passed:

```text
vite build completed successfully
```

## Notes

The refactor intentionally preserves legacy `/api/v1/shop/*` routes to avoid breaking the existing tests and older frontend integrations. New development should use the service-oriented routes.
