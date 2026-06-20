"""Optional OpenTelemetry setup for enterprise microservices."""

from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from ..config import enterprise_settings


def configure_tracing(app: FastAPI, service_name: str, engines: list[Engine] | None = None) -> None:
    """Enable tracing if OpenTelemetry packages are installed and OTEL_ENABLED=true.

    The function is intentionally safe in student/local environments. Missing
    optional packages do not break startup; the app continues with request id
    headers from the normal middleware.
    """
    if not enterprise_settings.otel_enabled:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except Exception:
        return

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.namespace": enterprise_settings.otel_service_namespace,
            "deployment.environment": enterprise_settings.app_environment,
            "service.instance.id": enterprise_settings.service_instance_name or service_name,
        }
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=enterprise_settings.otel_exporter_otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)

    for engine in engines or []:
        SQLAlchemyInstrumentor().instrument(engine=engine)
