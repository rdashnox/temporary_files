"""Local API gateway for no-Docker microservice testing.

This gateway is intentionally lightweight. It lets Windows/local students run the
same 3-node microservice layout without Docker Desktop by forwarding requests to
local Uvicorn service processes:

- Auth/Login:        127.0.0.1:8101, 8102, 8103
- Order:             127.0.0.1:8201, 8202, 8203
- Inventory:         127.0.0.1:8301, 8302, 8303
- Notification:      127.0.0.1:8401, 8402, 8403

If one node is down, the gateway retries the next node in the same service pool.
Docker/Nginx is still the recommended production option; this file is a local
fallback for development and demonstration.
"""

from __future__ import annotations

import asyncio
import json
import os
from itertools import count
from time import perf_counter
from typing import Iterable
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from .core.config import settings

DEFAULT_SERVICE_POOLS: dict[str, list[str]] = {
    "auth-service": [
        "http://127.0.0.1:8101",
        "http://127.0.0.1:8102",
        "http://127.0.0.1:8103",
    ],
    "order-service": [
        "http://127.0.0.1:8201",
        "http://127.0.0.1:8202",
        "http://127.0.0.1:8203",
    ],
    "inventory-service": [
        "http://127.0.0.1:8301",
        "http://127.0.0.1:8302",
        "http://127.0.0.1:8303",
    ],
    "notification-service": [
        "http://127.0.0.1:8401",
        "http://127.0.0.1:8402",
        "http://127.0.0.1:8403",
    ],
}


def _load_service_pools() -> tuple[dict[str, list[str]], str]:
    """Load dynamic local service ports selected by start-microservices-local.ps1.

    Windows can reserve or block common development ports. The startup script
    probes safe fallback ports and passes them through SERVICE_POOLS_JSON so the
    gateway always knows where each replica is actually running.
    """
    raw_value = os.getenv("SERVICE_POOLS_JSON")
    if not raw_value:
        return DEFAULT_SERVICE_POOLS, "default-static-ports"

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return DEFAULT_SERVICE_POOLS, "invalid-env-json-using-defaults"

    if not isinstance(parsed, dict):
        return DEFAULT_SERVICE_POOLS, "invalid-env-shape-using-defaults"

    pools: dict[str, list[str]] = {}
    for service_name, nodes in parsed.items():
        if not isinstance(service_name, str) or not isinstance(nodes, list):
            return DEFAULT_SERVICE_POOLS, "invalid-env-node-shape-using-defaults"
        node_urls = [node for node in nodes if isinstance(node, str) and node.startswith("http")]
        if not node_urls:
            return DEFAULT_SERVICE_POOLS, "empty-env-node-list-using-defaults"
        pools[service_name] = node_urls

    for required_service in DEFAULT_SERVICE_POOLS:
        if required_service not in pools:
            return DEFAULT_SERVICE_POOLS, "missing-required-service-using-defaults"

    return pools, "SERVICE_POOLS_JSON"


SERVICE_POOLS, SERVICE_POOLS_SOURCE = _load_service_pools()

ROUTE_SERVICE_PREFIXES: tuple[tuple[str, str], ...] = (
    ("/api/v1/auth", "auth-service"),
    ("/api/v1/data", "auth-service"),
    ("/api/v1/database", "auth-service"),
    ("/api/v1/orders", "order-service"),
    ("/api/v1/shop", "order-service"),
    ("/api/v1/inventory", "inventory-service"),
    ("/api/v1/notifications", "notification-service"),
)

API_INDEX_PAYLOAD = {
    "message": "FinMark Enterprise Microservice API Gateway is running",
    "note": "This is the API base URL. Open one of the available endpoints below.",
    "health": "/api/v1/health",
    "ready": "/api/v1/ready",
    "service_info": "/api/v1/service-info",
    "available_prefixes": [prefix for prefix, _ in ROUTE_SERVICE_PREFIXES],
    "common_endpoints": {
        "login": "POST /api/v1/auth/token",
        "current_user": "GET /api/v1/auth/me",
        "products": "GET /api/v1/inventory/products",
        "checkout": "POST /api/v1/orders/checkout",
        "admin_order_list": "GET /api/v1/orders",
        "notifications": "GET /api/v1/notifications",
    },
}

# These response headers are managed by the gateway/client transport and should
# not be copied blindly from the upstream response.
HOP_BY_HOP_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "content-encoding",
}

HOP_BY_HOP_REQUEST_HEADERS = {
    "host",
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
}

_rr_counters = {service: count() for service in SERVICE_POOLS}
_rr_lock = asyncio.Lock()

app = FastAPI(
    title="FinMark Local Microservice API Gateway",
    version="5.0.0-local-enterprise-gateway-no-docker",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _resolve_service(path: str) -> str | None:
    for prefix, service_name in ROUTE_SERVICE_PREFIXES:
        if path == prefix or path.startswith(f"{prefix}/"):
            return service_name
    return None


async def _ordered_nodes(service_name: str) -> list[str]:
    """Return service nodes beginning with the next round-robin target."""
    nodes = SERVICE_POOLS[service_name]
    async with _rr_lock:
        start_index = next(_rr_counters[service_name]) % len(nodes)
    return nodes[start_index:] + nodes[:start_index]


def _clean_request_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    return {
        key: value
        for key, value in headers
        if key.lower() not in HOP_BY_HOP_REQUEST_HEADERS
    }


def _clean_response_headers(headers: httpx.Headers) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_RESPONSE_HEADERS
    }


@app.middleware("http")
async def gateway_observability(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", uuid4().hex)
    started_at = perf_counter()
    response = await call_next(request)
    duration_ms = (perf_counter() - started_at) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-MS"] = f"{duration_ms:.2f}"
    response.headers["X-Service-Name"] = "local-api-gateway"
    response.headers["X-Service-Instance"] = "local-api-gateway-1"
    return response


@app.get("/")
def root():
    return {
        "message": "FinMark Local API Gateway is running",
        "mode": "no-docker-local-enterprise-microservices",
        "health": "/api/v1/health",
        "ready": "/api/v1/ready",
        "service_info": "/api/v1/service-info",
    }


@app.get("/api/v1")
@app.get("/api/v1/")
def api_index():
    return API_INDEX_PAYLOAD


@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "service": "local-api-gateway",
        "message": "Gateway is running. Use /api/v1/ready to check service nodes.",
        "service_pools_source": SERVICE_POOLS_SOURCE,
    }


@app.get("/api/v1/service-info")
def service_info():
    return {
        "service": "local-api-gateway",
        "deployment_mode": "local-enterprise-microservices-no-docker",
        "architecture": "database-per-service",
        "service_databases": ["auth", "order", "inventory", "notification"],
        "message_queue": "outbox/local fallback; RabbitMQ in Docker/cloud mode",
        "target_replicas_per_microservice": 3,
        "backup_nodes_after_one_failure": 2,
        "service_pools_source": SERVICE_POOLS_SOURCE,
        "service_pools": SERVICE_POOLS,
        "routing": {prefix: service for prefix, service in ROUTE_SERVICE_PREFIXES},
    }


@app.get("/api/v1/ready")
async def ready():
    results: dict[str, list[dict[str, object]]] = {}
    ready_nodes = 0
    total_nodes = sum(len(nodes) for nodes in SERVICE_POOLS.values())

    async with httpx.AsyncClient(timeout=httpx.Timeout(2.0, connect=1.0)) as client:
        for service_name, nodes in SERVICE_POOLS.items():
            service_results: list[dict[str, object]] = []
            for node_url in nodes:
                try:
                    response = await client.get(f"{node_url}/api/v1/health")
                    ok = response.status_code == 200
                    if ok:
                        ready_nodes += 1
                    service_results.append(
                        {"node": node_url, "status_code": response.status_code, "ready": ok}
                    )
                except httpx.HTTPError as exc:
                    service_results.append(
                        {"node": node_url, "ready": False, "error": exc.__class__.__name__}
                    )
            results[service_name] = service_results

    status_code = 200 if ready_nodes == total_nodes else 207 if ready_nodes else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if ready_nodes == total_nodes else "partial" if ready_nodes else "not_ready",
            "ready_nodes": ready_nodes,
            "total_nodes": total_nodes,
            "nodes": results,
        },
    )


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_request(full_path: str, request: Request):
    path = "/" + full_path
    service_name = _resolve_service(path)
    if service_name is None:
        return JSONResponse(
            status_code=404,
            content={
                "detail": "No local microservice route matched this path.",
                "path": path,
                "available_prefixes": [prefix for prefix, _ in ROUTE_SERVICE_PREFIXES],
            },
        )

    body = await request.body()
    headers = _clean_request_headers(request.headers.items())
    headers.setdefault("X-Forwarded-Host", request.headers.get("host", "127.0.0.1:8000"))
    query = request.url.query

    attempted_nodes: list[str] = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=3.0)) as client:
        for node_url in await _ordered_nodes(service_name):
            attempted_nodes.append(node_url)
            upstream_url = f"{node_url}{path}"
            if query:
                upstream_url = f"{upstream_url}?{query}"

            try:
                upstream_response = await client.request(
                    request.method,
                    upstream_url,
                    content=body,
                    headers=headers,
                )
                response_headers = _clean_response_headers(upstream_response.headers)
                response_headers["X-Upstream-Service"] = service_name
                response_headers["X-Upstream-Node"] = node_url
                response_headers["X-Attempted-Nodes"] = ",".join(attempted_nodes)
                return Response(
                    content=upstream_response.content,
                    status_code=upstream_response.status_code,
                    headers=response_headers,
                    media_type=upstream_response.headers.get("content-type"),
                )
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RemoteProtocolError):
                # Try the next replica. If one service node is down, two backups remain.
                continue

    return JSONResponse(
        status_code=503,
        content={
            "detail": f"All local nodes for {service_name} are unavailable.",
            "service": service_name,
            "attempted_nodes": attempted_nodes,
            "suggestion": "Run .\\start-microservices-local.ps1 again or inspect logs under logs\\microservices.",
        },
    )
