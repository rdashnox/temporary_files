# FinMark Full Enterprise Microservice Upgrade

## Objective

Upgrade the project from a microservice-style deployment with one shared database into a fuller enterprise microservice system with:

- separate Auth DB, Order DB, Inventory DB, and Notification DB
- message queue based asynchronous communication
- service-to-service authentication
- distributed tracing hooks
- formal database migration management
- 3-node/replica deployment per API microservice

## Enterprise Architecture

```text
React Frontend
   ↓
Nginx API Gateway / Local Python Gateway
   ↓
Auth Service x3  ───────────────→ Auth DB
Order Service x3 ───────────────→ Order DB
Inventory Service x3 ───────────→ Inventory DB
Notification Service x3 ────────→ Notification DB
   ↓                         ↑
RabbitMQ Event Bus ──────────┘
   ↓
Jaeger / OpenTelemetry tracing
```

## Service Databases

The old version used one shared database. The enterprise version now has dedicated database URLs:

```env
AUTH_DATABASE_URL=mysql+pymysql://user:password@host:3306/finmark_auth_db
ORDER_DATABASE_URL=mysql+pymysql://user:password@host:3306/finmark_order_db
INVENTORY_DATABASE_URL=mysql+pymysql://user:password@host:3306/finmark_inventory_db
NOTIFICATION_DATABASE_URL=mysql+pymysql://user:password@host:3306/finmark_notification_db
```

Each service has its own SQLAlchemy engine, session factory, and declarative model base:

| Service | Database | SQLAlchemy Base |
|---|---|---|
| Auth | `finmark_auth_db` | `AuthBase` |
| Order | `finmark_order_db` | `OrderBase` |
| Inventory | `finmark_inventory_db` | `InventoryBase` |
| Notification | `finmark_notification_db` | `NotificationBase` |

There are no cross-database foreign keys. Cross-service references are stored as IDs, such as `user_id` and `product_id`.

## New Enterprise Backend Files

```text
backend/enterprise/config.py
backend/enterprise/databases.py
backend/enterprise/models.py
backend/enterprise/app_factory.py
backend/enterprise/events.py
backend/enterprise/security/service_auth.py
backend/enterprise/security/user_auth.py
backend/enterprise/observability/tracing.py
backend/enterprise/routes/auth.py
backend/enterprise/routes/orders.py
backend/enterprise/routes/inventory.py
backend/enterprise/routes/notifications.py
backend/enterprise/routes/shop.py
backend/enterprise/routes/data.py
backend/enterprise/services/auth_enterprise_service.py
backend/enterprise/services/order_enterprise_service.py
backend/enterprise/services/inventory_enterprise_service.py
backend/enterprise/services/notification_enterprise_service.py
backend/enterprise/scripts/init_enterprise_databases.py
backend/enterprise/scripts/publish_pending_outbox.py
backend/enterprise/scripts/notification_consumer.py
backend/enterprise/migrations/auth
backend/enterprise/migrations/order
backend/enterprise/migrations/inventory
backend/enterprise/migrations/notification
```

## Message Queue

RabbitMQ was added as the enterprise message broker.

Exchange:

```text
finmark.events
```

Current event types:

```text
order.created
inventory.low_stock
```

The Order service writes order events into its Order DB outbox table and publishes to RabbitMQ. The Notification worker consumes these events and writes notification records into the Notification DB.

Outbox tables were added to avoid losing events when RabbitMQ is temporarily unavailable:

```text
order_outbox_events
inventory_outbox_events
```

Pending outbox events can be retried using:

```powershell
python -m backend.enterprise.scripts.publish_pending_outbox
```

## Service-to-Service Authentication

Internal endpoints are protected with `X-Service-Token`.

The service token is a short-lived JWT signed with:

```env
SERVICE_AUTH_SECRET=replace-this-with-a-long-random-service-token-secret
SERVICE_AUTH_ALGORITHM=HS256
SERVICE_TOKEN_EXPIRE_MINUTES=10
```

Protected internal endpoints include:

```text
GET  /api/v1/inventory/internal/products/{product_id}
POST /api/v1/inventory/internal/reserve-stock
POST /api/v1/notifications/internal/events
```

This prevents random external clients from calling internal microservice operations directly.

## Distributed Tracing

OpenTelemetry hooks were added. In Docker mode, Jaeger is included.

Jaeger UI:

```text
http://127.0.0.1:16686
```

Enable tracing with:

```env
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
OTEL_SERVICE_NAMESPACE=finmark
```

If OpenTelemetry packages are missing or `OTEL_ENABLED=false`, the app still runs using request ID headers:

```text
X-Request-ID
X-Process-Time-MS
X-Service-Name
X-Service-Instance
```

## Formal Migration Management

Alembic migration folders were added per service:

```text
backend/enterprise/migrations/auth
backend/enterprise/migrations/order
backend/enterprise/migrations/inventory
backend/enterprise/migrations/notification
```

Run all service migrations with:

```powershell
python -m backend.enterprise.scripts.run_enterprise_migrations
```

Or run each service migration separately:

```powershell
python -m alembic -c backend/enterprise/migrations/auth/alembic.ini upgrade head
python -m alembic -c backend/enterprise/migrations/order/alembic.ini upgrade head
python -m alembic -c backend/enterprise/migrations/inventory/alembic.ini upgrade head
python -m alembic -c backend/enterprise/migrations/notification/alembic.ini upgrade head
```

For school/local demo mode, the project still supports auto-creation using:

```env
AUTO_CREATE_DB=true
```

For production, use:

```env
AUTO_CREATE_DB=false
SEED_DEMO_DATA=false
```

## Docker Enterprise Deployment

Run:

```powershell
.\start-microservices.ps1
```

Docker mode starts:

- Auth MySQL
- Order MySQL
- Inventory MySQL
- Notification MySQL
- RabbitMQ
- Jaeger
- 3 Auth service nodes
- 3 Order service nodes
- 3 Inventory service nodes
- 3 Notification service nodes
- Notification event worker
- Nginx API Gateway

Gateway:

```text
http://127.0.0.1:8000
```

RabbitMQ UI:

```text
http://127.0.0.1:15672
```

Jaeger UI:

```text
http://127.0.0.1:16686
```

## No-Docker Local Enterprise Mode

If Docker is not installed, the project falls back to local Uvicorn processes:

```powershell
.\start-microservices-local.ps1
```

Local mode uses four SQLite databases under:

```text
data/enterprise-local/
```

This allows you to demonstrate database-per-service microservices even without Docker Desktop.

## Default Local Admin Account

```text
Username: admin@example.com
Password: Admin@12345
```

## Important Production Notes

This package is now much closer to enterprise design, but a real production launch still needs:

1. secret rotation and vault-based secret management
2. HTTPS/TLS certificates
3. private Docker network/firewall rules
4. CI/CD pipeline for migrations and deployment
5. backup and restore strategy per database
6. centralized logs and metrics
7. stronger saga/compensation logic for distributed checkout failures

## Validation Performed

- Python compile check passed
- Backend tests passed: 21 tests
- Enterprise separated SQLite database initialization passed
- Docker Compose YAML parsed successfully
- Frontend Vite production build passed after installing frontend dependencies

## Alembic Migration Dependency Fix

If you see this error:

```text
ModuleNotFoundError: No module named 'alembic'
```

Run this from the project root:

```powershell
.\install-enterprise-deps.ps1
```

Then run local enterprise migrations:

```powershell
.\run-enterprise-migrations.ps1
```

Or run the Python command directly after installing requirements:

```powershell
.\.venv\Scripts\python.exe -m backend.enterprise.scripts.run_enterprise_migrations --local
```

For production/MySQL migration mode, configure the four database URLs first and run without `--local`.

See `ALEMBIC_MIGRATION_DEPENDENCY_FIX.md` for details.

## Windows `[WinError 10013]` Socket Fix

If Windows blocks the gateway or service ports, run:

```powershell
.\stop-microservices-local.ps1
.\start-microservices-local.ps1
```

The local startup script now probes ports before starting Uvicorn. If `8000`, `8101`, `8201`, `8301`, or `8401` are blocked/reserved, it automatically uses safe fallback ports and writes the selected API URL to:

```text
frontend/.env.local
```

To diagnose blocked/reserved ports, run:

```powershell
.\diagnose-windows-ports.ps1
```

Then restart the frontend so Vite reads the updated `.env.local` file.
