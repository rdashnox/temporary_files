from __future__ import annotations

from contextlib import asynccontextmanager
from time import perf_counter
from typing import Iterable, Sequence
from uuid import uuid4

import anyio.to_thread
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import enterprise_settings
from .databases import get_engine_for_service, safe_url, service_database_urls
from .observability.tracing import configure_tracing
from ..validation import install_validation_exception_handlers

RouterSpec = tuple[APIRouter, str, Sequence[str]]


def create_enterprise_service_app(
    *,
    service_name: str,
    service_slug: str,
    service_key: str,
    router_specs: Iterable[RouterSpec],
    version: str = "5.0.0-enterprise-microservices",
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        anyio.to_thread.current_default_thread_limiter().total_tokens = enterprise_settings.threadpool_tokens
        yield

    app = FastAPI(title=f"FinMark {service_name} Enterprise Service API", version=version, lifespan=lifespan)
    install_validation_exception_handlers(app, service_slug=service_slug)
    app.add_middleware(GZipMiddleware, minimum_size=enterprise_settings.gzip_minimum_size)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=enterprise_settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    engine = get_engine_for_service(service_key)
    configure_tracing(app, service_slug, [engine])

    @app.middleware("http")
    async def request_observability_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", uuid4().hex)
        started_at = perf_counter()
        response = await call_next(request)
        duration_ms = (perf_counter() - started_at) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-MS"] = f"{duration_ms:.2f}"
        response.headers["X-Service-Name"] = service_slug
        response.headers["X-Service-Instance"] = enterprise_settings.service_instance_name or service_slug
        response.headers["X-Trace-Mode"] = "opentelemetry" if enterprise_settings.otel_enabled else "request-id"
        return response

    for router, prefix, tags in router_specs:
        app.include_router(router, prefix=prefix, tags=list(tags))

    @app.get("/api/v1/health")
    def health_check():
        return {
            "status": "ok",
            "service": service_slug,
            "service_key": service_key,
            "instance": enterprise_settings.service_instance_name or service_slug,
            "architecture": "enterprise-database-per-service",
            "environment": enterprise_settings.app_environment,
        }

    @app.get("/api/v1/ready")
    def readiness_check():
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "not_ready",
                    "service": service_slug,
                    "database": safe_url(str(engine.url)),
                    "message": "Service database is not reachable.",
                },
            ) from exc
        return {
            "status": "ready",
            "service": service_slug,
            "database": safe_url(str(engine.url)),
            "database_isolation": "dedicated-service-database",
            "pool_size": enterprise_settings.db_pool_size,
            "max_overflow": enterprise_settings.db_max_overflow,
        }

    @app.get("/api/v1/service-info")
    def service_info():
        return {
            "service": service_slug,
            "service_name": service_name,
            "service_key": service_key,
            "instance": enterprise_settings.service_instance_name or service_slug,
            "replicas_per_service": enterprise_settings.service_replicas,
            "target_replicas_per_microservice": enterprise_settings.service_replicas,
            "backup_nodes_after_one_failure": max(enterprise_settings.service_replicas - 1, 0),
            "database_per_service": True,
            "message_queue": "RabbitMQ topic exchange finmark.events",
            "service_to_service_auth": "X-Service-Token JWT",
            "distributed_tracing": "OpenTelemetry optional" if enterprise_settings.otel_enabled else "request-id headers active; enable OTEL_ENABLED=true for OpenTelemetry",
            "databases": service_database_urls(),
            "version": version,
        }

    @app.get("/")
    def read_root():
        return {"message": f"Welcome to FinMark {service_name} Enterprise Service API", "service": service_slug}

    return app
