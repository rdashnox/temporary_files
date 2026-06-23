from contextlib import asynccontextmanager
from time import perf_counter
from typing import Iterable, Sequence
from uuid import uuid4

import anyio.to_thread
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .core.config import settings
from .database import engine, init_db, safe_database_url, session_scope
from .services.seed_service import seed_database
from .validation import install_validation_exception_handlers

RouterSpec = tuple[APIRouter, str, Sequence[str]]


def create_service_app(
    *,
    service_name: str,
    service_slug: str,
    router_specs: Iterable[RouterSpec],
    version: str = "4.0.0-microservice-3-node",
) -> FastAPI:
    """Create a FastAPI app for one deployable service node.

    The codebase can still run as one development app through backend.main:app,
    but production/local Docker can start each core capability as its own app:
    auth, order, inventory, and notification. Each app has the same health,
    readiness, CORS, compression, tracing, and database-pool behavior.
    """

    enterprise_mode_requested = (
        settings.enterprise_microservices_enabled
        or settings.has_full_enterprise_database_urls
        or settings.db_user.strip().lower() == "finmark_app"
    )

    if service_slug == "platform-monolith" and enterprise_mode_requested:
        app = FastAPI(
            title="FinMark Enterprise Microservices Guard API",
            version=version,
            description=(
                "This project is configured for the full enterprise microservice mode. "
                "Start the gateway and service replicas instead of backend.main:app."
            ),
        )
        install_validation_exception_handlers(app, service_slug=service_slug)

        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.frontend_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        guidance = {
            "status": "wrong_start_command",
            "service": service_slug,
            "message": (
                "You started the legacy single-app backend with backend.main:app, "
                "but .env is configured for the full enterprise 4-database microservice mode."
            ),
            "why_it_failed_before": (
                "backend.main:app uses the legacy DB_NAME value, commonly finmark_db. "
                "The least-privilege finmark_app user is intentionally granted only to "
                "finmark_auth_db, finmark_order_db, finmark_inventory_db, and "
                "finmark_notification_db."
            ),
            "correct_commands": [
                ".\\stop-microservices-local.ps1",
                ".\\repair-enterprise-env.ps1",
                ".\\verify-enterprise-mysql-databases.ps1",
                ".\\seed-enterprise-mysql.ps1",
                ".\\start-microservices-local-mysql.ps1",
                ".\\start-frontend.ps1",
            ],
            "do_not_use_for_enterprise_mode": (
                "python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"
            ),
            "legacy_override": (
                "If you intentionally want the old monolith, run .\\start-backend.ps1 -Legacy "
                "and grant DB_USER access to DB_NAME, or change DB_NAME to a database that user can access."
            ),
        }

        @app.get("/")
        def enterprise_mode_root():
            return guidance

        @app.get("/api/v1/health")
        def enterprise_mode_health():
            return guidance

        @app.get("/api/v1/service-info")
        def enterprise_mode_service_info():
            return guidance

        @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
        def enterprise_mode_wrong_command(path: str):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=guidance)

        return app

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        anyio.to_thread.current_default_thread_limiter().total_tokens = settings.threadpool_tokens

        # In normal local uvicorn development AUTO_CREATE_DB/SEED_DEMO_DATA are
        # true. In replicated Docker/Kubernetes deployment they are false and a
        # one-shot db-init job handles schema/seed work to avoid replica races.
        init_db()
        if settings.seed_demo_data:
            with session_scope() as db:
                seed_database(db)
        yield

    app = FastAPI(
        title=f"FinMark {service_name} Service API",
        version=version,
        lifespan=lifespan,
    )
    install_validation_exception_handlers(app, service_slug=service_slug)

    app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)

    if settings.allowed_hosts and settings.allowed_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_observability_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", uuid4().hex)
        service_instance = settings.service_instance_name or service_slug
        started_at = perf_counter()
        response = await call_next(request)
        duration_ms = (perf_counter() - started_at) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-MS"] = f"{duration_ms:.2f}"
        response.headers["X-Service-Name"] = service_slug
        response.headers["X-Service-Instance"] = service_instance
        return response

    for router, prefix, tags in router_specs:
        app.include_router(router, prefix=prefix, tags=list(tags))

    @app.get("/api/v1/health")
    def health_check():
        """Cheap liveness probe. It intentionally does not touch the database."""
        return {
            "status": "ok",
            "service": service_slug,
            "instance": settings.service_instance_name or service_slug,
            "message": f"{service_name} service is running",
            "environment": settings.app_environment,
        }

    @app.get("/api/v1/ready")
    def readiness_check():
        """Readiness probe for load balancers; confirms database connectivity."""
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "not_ready",
                    "service": service_slug,
                    "database": safe_database_url(),
                    "message": "Database is not reachable.",
                },
            ) from exc

        return {
            "status": "ready",
            "service": service_slug,
            "instance": settings.service_instance_name or service_slug,
            "database": safe_database_url(),
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
        }

    @app.get("/api/v1/service-info")
    def service_info():
        """Expose non-sensitive service identity for load-balancer checks."""
        return {
            "service": service_slug,
            "service_name": service_name,
            "instance": settings.service_instance_name or service_slug,
            "deployment_mode": settings.deployment_mode,
            "target_replicas_per_microservice": settings.service_replicas,
            "backup_nodes_after_one_failure": max(settings.service_replicas - 1, 0),
            "version": version,
        }

    @app.get("/")
    def read_root():
        return {
            "message": f"Welcome to FinMark {service_name} Service API",
            "service": service_slug,
            "health": "/api/v1/health",
            "ready": "/api/v1/ready",
            "service_info": "/api/v1/service-info",
        }

    return app
