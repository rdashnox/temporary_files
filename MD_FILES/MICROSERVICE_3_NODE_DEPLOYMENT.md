# FinMark 3-Node Microservice Deployment

## Objective

This version turns the core FinMark backend into a microservice-style deployment where each core service has **3 independent nodes/replicas**:

| Microservice | Responsibility | Nodes |
|---|---:|---:|
| Auth/Login Service | Login, registration, token refresh, session validation | 3 |
| Order Service | Checkout, order listing, order CRUD, legacy `/shop/checkout` support | 3 |
| Inventory Service | Product catalog, product lookup, stock summary | 3 |
| Notification Service | In-app notifications and read/unread actions | 3 |

Total backend service nodes: **12 FastAPI containers**. If one node of a microservice goes down, Nginx keeps routing traffic to the remaining **2 healthy nodes**.

## Architecture

```text
Browser / React Frontend
        |
        v
Nginx API Gateway :8000
        |
        +--> auth-service-1 / auth-service-2 / auth-service-3
        |
        +--> order-service-1 / order-service-2 / order-service-3
        |
        +--> inventory-service-1 / inventory-service-2 / inventory-service-3
        |
        +--> notification-service-1 / notification-service-2 / notification-service-3
        |
        v
Shared MySQL Database
```

## What was changed in the code

### 1. Shared app factory

Added:

```text
backend/app_factory.py
```

This prevents duplicate FastAPI setup code. Every service node now gets the same:

- CORS setup
- GZip compression
- request tracing headers
- liveness endpoint
- readiness endpoint
- service identity endpoint
- database pool behavior

### 2. Microservice entrypoints

Added:

```text
backend/microservices/auth_main.py
backend/microservices/order_main.py
backend/microservices/inventory_main.py
backend/microservices/notification_main.py
```

Each file starts only the routers needed by that microservice.

### 3. 3-node Docker Compose deployment

Added:

```text
docker-compose.microservices.yml
deployment/Dockerfile.microservice
deployment/nginx.microservices.conf
start-microservices.ps1
stop-microservices.ps1
```

### 4. Cloud/Kubernetes-ready deployment

Added:

```text
deployment/k8s/finmark-microservices.yaml
```

Each Kubernetes deployment uses:

```yaml
replicas: 3
```

for every core microservice.

## How to run locally with Docker

From the project root:

```powershell
.\start-microservices.ps1
```

Or manually:

```powershell
docker compose -f docker-compose.microservices.yml up --build -d
```

The gateway will be available at:

```text
http://127.0.0.1:8000/api/v1/health
```

Then run the frontend normally:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## How to confirm load balancing

Run this several times:

```powershell
curl http://127.0.0.1:8000/api/v1/auth/token
```

That exact command returns `405 Method Not Allowed` because login requires POST, but the response headers should still show which service handled it:

```text
X-Service-Name: auth-service
X-Service-Instance: auth-service-1/auth-service-2/auth-service-3
```

For a JSON service identity check:

```powershell
curl http://127.0.0.1:8000/api/v1/service-info
```

For each direct service identity, use Docker logs:

```powershell
docker compose -f docker-compose.microservices.yml logs microservice-gateway
```

Nginx logs show the upstream container used for each request.

## How to test failover

Stop one node, for example:

```powershell
docker compose -f docker-compose.microservices.yml stop order-service-1
```

Then continue using checkout. The gateway will route order traffic to:

```text
order-service-2
order-service-3
```

Bring the node back:

```powershell
docker compose -f docker-compose.microservices.yml start order-service-1
```

## Why DB initialization is separated

In a replicated setup, all 12 service nodes should not create/alter/seed the database at the same time. This version adds a one-shot container:

```text
db-init
```

It runs before the service replicas and performs:

- schema creation
- safe local schema upgrade
- demo seed data

The service replicas run with:

```env
AUTO_CREATE_DB=false
SEED_DEMO_DATA=false
```

This prevents database startup race conditions.

## Important production note

This is a **microservice-style deployment** using one shared codebase and one shared database. That is the safest next step for your current project.

A more advanced enterprise version would eventually separate databases per service:

- auth database
- order database
- inventory database
- notification database

That next level requires API contracts, asynchronous events, service-to-service authentication, distributed tracing, and database migration management.

## Recommended next improvements

1. Add Redis for token blacklist/cache and rate limiting.
2. Add RabbitMQ or Kafka so Order Service can publish events to Notification Service asynchronously.
3. Add Alembic migrations instead of startup schema compatibility upgrades.
4. Add API gateway rate limiting and request size limits per route.
5. Add OpenTelemetry tracing across services.
6. Add CI/CD pipeline that runs backend tests, frontend build, Docker build, and load tests.

---

## No-Docker Local Fallback

If PowerShell shows `docker : The term 'docker' is not recognized`, Docker Desktop is not available on your computer.

This package now includes a local fallback:

```powershell
.\start-microservices-local.ps1
```

This starts 12 local Uvicorn processes and one Python API gateway:

- Auth/Login x3: ports 8101, 8102, 8103
- Order x3: ports 8201, 8202, 8203
- Inventory x3: ports 8301, 8302, 8303
- Notification x3: ports 8401, 8402, 8403
- API Gateway: port 8000

The original command also now detects missing Docker and automatically falls back:

```powershell
.\start-microservices.ps1
```

Stop local services with:

```powershell
.\stop-microservices-local.ps1
```
