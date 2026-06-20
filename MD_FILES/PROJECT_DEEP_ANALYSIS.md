# FinMark Deep Project Analysis and UI Upgrade Notes

## Current project assessment

FinMark is currently a clean authentication-first prototype. The backend uses FastAPI with JWT access and refresh tokens, email verification, password reset, and a protected route. The frontend is plain HTML, CSS, and JavaScript. This is a good foundation for a school or early-stage milestone because it is easy to run, easy to understand, and does not require a complex frontend build tool.

However, the existing dashboard was only a placeholder. For the requested business system scope, the application needs to evolve from an auth prototype into a modular business platform with dashboards, order workflows, reporting, planning approvals, RBAC, and marketing analytics.

## UI upgrade added

The dashboard has been replaced with a full executive business dashboard UI covering:

1. Dashboard & Business Intelligence
2. Order Management
3. Financial Analysis & Reporting
4. Planning Request workflow
5. User & Role Management
6. Marketing Analytics

The new UI includes:

- Sidebar navigation
- Global module search
- KPI summary cards
- Dashboard period controls
- BI performance chart
- Order lifecycle board
- Report builder and async job queue mockup
- Planning request workflow UI
- RBAC permission matrix
- Security backlog checklist
- Marketing funnel and channel ROI cards
- Responsive layout for desktop, tablet, and mobile

A new protected backend endpoint was also added:

```text
GET /api/v1/data/business-modules
```

This returns pre-shaped dashboard data after bearer-token validation. In production, this endpoint should read from cached or pre-aggregated analytics models instead of calculating every metric directly from raw transactional tables.

## Architecture analysis by module

### 1. Dashboard & Business Intelligence

Current risk: dashboards will become slow if every KPI is calculated live from transactional tables. The target of under 3 seconds will be difficult if the system queries orders, payments, reports, users, and marketing events directly on every page load.

Recommended approach:

- Create pre-aggregated dashboard tables or materialized views.
- Return small KPI payloads first, then lazy-load charts.
- Use cache keys by user role, tenant, date range, and permission scope.
- Use WebSocket or Server-Sent Events for live counters, with polling fallback.
- Track dashboard API latency and cache hit rate.

Suggested data flow:

```text
Transactional DB -> Event/Job Processor -> Aggregated Metrics Store -> Dashboard API -> UI
```

### 2. Order Management

Current risk: the ProductCatalog will lag when more than 200 items are loaded at once, especially on mobile. A catalog should never load all records and all images at once.

Recommended approach:

- Use server-side pagination and filtering.
- Add virtual scrolling for long product lists.
- Use compressed thumbnails and lazy-loaded images.
- Add cart coupon validation as a backend service, not only frontend logic.
- Make checkout idempotent so duplicate clicks do not create duplicate orders.
- Add order status events for payment, packing, shipping, cancellation, refund, and exception handling.
- Add webhooks with retry and dead-letter handling.

Suggested order lifecycle:

```text
Cart -> Checkout Started -> Payment Pending -> Paid -> Packed -> Shipped -> Delivered
                                     -> Payment Failed / Cancelled / Refunded / Exception
```

### 3. Financial Analysis & Reporting

Current risk: static reports will not scale once users need exports, filters, APIs, and long-running calculations.

Recommended approach:

- Use asynchronous report generation for heavy reports.
- Return a report job ID immediately.
- Let the frontend poll job status or subscribe to report completion events.
- Store report outputs in object storage or a generated-files table.
- Provide export formats such as CSV, Excel, PDF, and API JSON.
- Enforce RBAC on every report query.

Suggested report flow:

```text
User request -> Validate permission -> Create report job -> Queue worker -> Store result -> Notify user
```

### 4. Planning Request

Current risk: approvals can become unreliable if workflow state is only stored as a simple status text.

Recommended approach:

- Model planning requests as a workflow state machine.
- Record every transition with timestamp, actor, previous state, next state, and remarks.
- Support mobile approval actions with secure confirmation.
- Add SLA monitoring for pending approvals.
- Prevent invalid transitions such as approving an already rejected request.

Suggested states:

```text
Draft -> Submitted -> Validated -> Manager Review -> Finance Approval -> Approved -> Released
                                             -> Rejected / Cancelled / Needs Revision
```

### 5. User & Role Management

Current risk: the project has authentication, but the business platform needs authorization. Login only proves identity; RBAC decides what the user can access.

Recommended approach:

- Create users, roles, permissions, and user_role tables.
- Enforce permissions in backend dependencies/middleware.
- Add 2FA/MFA, login rate limiting, password reset throttling, and audit logs.
- Avoid storing JWTs in localStorage for high-security production apps; prefer secure HttpOnly cookies where possible.
- Prepare `tenant_id` isolation early if SME multi-tenant support is planned.

Suggested permission model:

```text
User -> UserRole -> Role -> RolePermission -> Permission
Tenant -> Users / Orders / Reports / Planning Requests
```

### 6. Marketing Analytics

Current risk: marketing data often comes from external systems and arrives late, duplicated, or with inconsistent attribution.

Recommended approach:

- Create ingestion pipelines for campaign, ad spend, traffic, customer behavior, and conversion data.
- Normalize customer/session identifiers.
- Connect campaign data to order revenue.
- Track funnel stages from visit to product view, cart add, checkout, and paid order.
- Add ROI, CAC, conversion rate, and campaign cohort analysis.

Suggested marketing analytics flow:

```text
Ad Platforms / Website Events / Orders -> Ingestion -> Normalization -> Attribution -> Marketing Dashboard
```

## Major technical recommendations

### Backend

- Replace in-memory users with a database.
- Add migrations using Alembic.
- Add RBAC dependency helpers such as `require_permission("finance.report.read")`.
- Add rate limiting for login, register, forgot password, and refresh token endpoints.
- Add audit logging for login, logout, report exports, role changes, and approvals.
- Add structured logging and error monitoring.
- Add async background processing with Celery, RQ, Dramatiq, or FastAPI background workers for small workloads.

### Frontend

- Keep the current no-build frontend for prototype simplicity.
- If the app grows, move to a component-based framework such as React, Vue, or Svelte.
- Split dashboard modules into separate JS files when logic becomes larger.
- Add loading skeletons and empty states.
- Add role-aware menu visibility.
- Add client-side route guards per module, but never rely on frontend checks alone.

### Database and performance

- Use proper indexes for order status, created_at, user_id, tenant_id, and report filters.
- Do not run heavy report queries directly during HTTP requests.
- Use Redis or a similar cache for dashboard summaries.
- Use materialized views or summary tables for BI metrics.
- Use background jobs for exports and financial reports.

### Security

- Add 2FA/MFA.
- Add login throttling and account lockout controls.
- Use secure secret management.
- Add refresh token rotation and revocation.
- Add admin audit logs.
- Enforce tenant isolation on every data query.
- Review CORS settings before production.

## Suggested next implementation order

1. Add database models for users, roles, permissions, orders, reports, planning requests, and audit logs.
2. Move auth data from memory to database.
3. Implement RBAC permission checks on backend routes.
4. Add order management APIs with pagination and status updates.
5. Add report job queue and export endpoints.
6. Add planning request workflow tables and approval endpoints.
7. Add dashboard aggregation jobs and cached summary APIs.
8. Add marketing event ingestion and funnel reporting.
9. Add end-to-end tests for auth, RBAC, checkout, reporting, and approvals.
10. Add monitoring for API latency, failed jobs, failed webhooks, and security events.
