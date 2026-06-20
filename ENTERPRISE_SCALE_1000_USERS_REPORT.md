# Enterprise Scale Refactor Report — 1,000 Active Users

## Corrected Objective

Make the FinMark application capable of supporting up to **1,000 active users using the app at the same time**, especially users who are actively browsing products, reading notifications, and placing orders.

## Expert Assessment

The previous SOA version was good for local/demo use, but it was not yet production-ready for 1,000 active concurrent users because the following areas needed hardening:

1. **Database connection control** — without explicit pooling, traffic spikes can exhaust MySQL connections.
2. **Blocking database work inside async routes** — sync SQLAlchemy calls inside `async def` routes can block the event loop.
3. **Duplicate checkout risk** — retries during slow network conditions can create duplicate orders.
4. **Lack of readiness checks** — load balancers need a DB-aware readiness endpoint.
5. **Limited observability** — production traffic needs request IDs and processing time headers.
6. **No load testing setup** — 1,000-user support must be validated, not assumed.
7. **No production deployment profile** — local `--reload` mode is not suitable for high-traffic use.

## Refactor Completed

### 1. Backend scalability improvements

Updated files:

```text
backend/core/config.py
backend/database.py
backend/main.py
backend/routes/auth.py
backend/routes/data.py
backend/routes/database_entities.py
backend/routes/inventory.py
backend/routes/orders.py
backend/routes/notifications.py
backend/routes/shop.py
backend/services/order_service.py
backend/services/shop_service.py
backend/models.py
backend/schemas/shop.py
```

Changes made:

- Added environment-driven SQLAlchemy pool configuration:
  - `DB_POOL_SIZE`
  - `DB_MAX_OVERFLOW`
  - `DB_POOL_TIMEOUT`
  - `DB_POOL_RECYCLE`
  - `DB_CONNECT_TIMEOUT`
- Added `AUTO_CREATE_DB=false` support for production so every worker does not run `create_all()`.
- Added `THREADPOOL_TOKENS` to increase FastAPI/AnyIO thread capacity for sync database work.
- Converted database-heavy route handlers from `async def` to `def`, allowing FastAPI to run blocking SQLAlchemy work safely in its threadpool.
- Added GZip response compression.
- Added request tracing headers:
  - `X-Request-ID`
  - `X-Process-Time-MS`
- Added `TrustedHostMiddleware` support through `ALLOWED_HOSTS`.
- Added short product catalog cache headers.
- Added retry-safe checkout idempotency.

### 2. New production health endpoints

```text
GET /api/v1/health
GET /api/v1/ready
GET /api/v1/scale/profile
```

Purpose:

- `/health` checks if the API process is alive.
- `/ready` checks if the API can reach the database.
- `/scale/profile` exposes non-sensitive scalability settings for deployment checking.

### 3. Retry-safe checkout

New support:

```text
Idempotency-Key: checkout-unique-request-id
```

The frontend now sends an `Idempotency-Key` for checkout requests. If the same request is retried, the API returns the original order instead of creating a duplicate order.

Database model update:

```text
orders.idempotency_key
```

Migration file added:

```text
backend/scripts/enterprise_scale_migration.sql
```

### 4. Query/index improvements

Added indexes:

```text
ix_orders_idempotency_key
ix_orders_status_created_at
ix_orders_user_created_at
ix_notifications_user_created_at
```

These help common high-traffic operations:

- order lookup after checkout retry
- order list by status/date
- user order history
- user notification list

### 5. Frontend scalability improvements

Updated file:

```text
frontend/src/api/client.js
```

Changes made:

- Added request timeout support.
- Added product request caching.
- Added product request de-duplication so repeated product loads share one in-flight request.
- Added checkout `Idempotency-Key` support.
- Kept the existing refresh-token request lock.

New frontend environment variables:

```text
VITE_REQUEST_TIMEOUT_MS=15000
VITE_PRODUCT_CACHE_TTL_MS=60000
```

### 6. Load testing setup

Added files:

```text
loadtests/locustfile.py
loadtests/requirements-loadtest.txt
loadtests/README.md
backend/scripts/seed_load_test_users.py
```

Seed 1,000 users:

```powershell
python -m backend.scripts.seed_load_test_users --count 1000
```

Run load test:

```powershell
locust -f loadtests/locustfile.py --host http://127.0.0.1:8000 --users 1000 --spawn-rate 50 --run-time 10m
```

### 7. Production deployment files

Added files:

```text
start-production-api.ps1
start-production-linux.sh
deployment/Dockerfile.backend
deployment/nginx.conf
docker-compose.enterprise.yml
```

Recommended Linux/VPS command:

```bash
bash start-production-linux.sh
```

Recommended Windows production-like command:

```powershell
.\start-production-api.ps1
```

## Recommended Production Architecture

For 1,000 active users, do not run the app with `uvicorn --reload`.

Recommended architecture:

```text
Users
  ↓
Nginx / Cloud Load Balancer
  ↓
FastAPI API workers, 4 to 8 workers to start
  ↓
MySQL 8.x or PostgreSQL
```

Optional next enterprise step:

```text
Redis cache / Redis queue
Background worker for email, notification fan-out, and reports
Object storage for report files
CDN for frontend static files
```

## Initial Production Sizing Guide

For a starter VPS/cloud deployment:

| Component | Suggested Minimum |
|---|---:|
| API server | 4 vCPU, 8 GB RAM |
| Database server | 4 vCPU, 8–16 GB RAM |
| API workers | 4 workers first, then test 6–8 |
| DB pool per worker | 20 |
| DB overflow per worker | 40 |
| MySQL max connections | 250–300 minimum |
| Nginx worker connections | 4096 |

Important connection calculation:

```text
Potential DB connections = API workers × (DB_POOL_SIZE + DB_MAX_OVERFLOW)
```

Example:

```text
4 workers × (20 + 40) = 240 possible database connections
```

Your MySQL `max_connections` must be higher than this number, with room for admin tools and background jobs.

## Environment Configuration for Production

Example `.env` values:

```env
APP_ENV=production
SECRET_KEY=replace-with-a-long-random-production-secret
AUTO_CREATE_DB=false
SEED_DEMO_DATA=false
FRONTEND_ORIGINS=https://your-domain.com
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

DB_DRIVER=mysql+pymysql
DB_HOST=your-db-host
DB_PORT=3306
DB_NAME=finmark_db
DB_USER=finmark_app
DB_PASSWORD=strong_password_here

DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
DB_CONNECT_TIMEOUT=10
THREADPOOL_TOKENS=100
PRODUCT_CACHE_MAX_AGE_SECONDS=60
```

## Validation Results

Backend validation:

```text
20 passed
```

Frontend validation:

```text
Vite production build successful
```

New tests added:

```text
backend/tests/test_enterprise_scale.py
```

Covered:

- health endpoint
- readiness endpoint
- scale profile endpoint
- product cache headers
- checkout idempotency duplicate prevention

## Honest Limitation

The code is now prepared for a **1,000-active-user target**, but the exact capacity depends on the deployment server, database size, database tuning, network latency, and real user behavior. The correct way to prove capacity is to run the included Locust test on the actual server and tune workers, database connections, and database hardware based on the results.

## Next Recommended Improvements

1. Add Redis for shared rate limiting, token/session coordination, and product cache.
2. Move email sending and notification fan-out to a background worker.
3. Add Alembic migrations instead of SQL script migrations.
4. Add Prometheus/Grafana metrics.
5. Add Sentry or similar error monitoring.
6. Add CI/CD pipeline with automated backend tests and frontend build.
7. Move product inventory from static constants into a real `products` table with stock reservation logic.
8. Add optimistic or pessimistic stock locking for high-volume checkout.
9. Add API-level rate limiting for login and checkout.
10. Serve the frontend through Nginx/CDN with hashed assets and long cache headers.
