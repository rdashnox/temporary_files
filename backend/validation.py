from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _field_label(location: Any) -> str:
    """Convert FastAPI/Pydantic locations into user-readable field names."""
    if not isinstance(location, (list, tuple)):
        return str(location or "request")

    parts = [str(part) for part in location if part not in ("body", "query", "path", "header", "form")]
    if not parts:
        return "request"
    return ".".join(parts)


def _clean_message(message: str) -> str:
    replacements = {
        "Field required": "This field is required.",
        "Input should be a valid string": "This field must be text.",
        "Input should be a valid integer": "This field must be a whole number.",
        "Input should be a valid number": "This field must be a number.",
        "Input should be a valid boolean": "This field must be true or false.",
        "Input should be a valid list": "This field must be a list.",
    }
    return replacements.get(message, message)


def _validation_fields(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    fields: list[dict[str, str]] = []
    for error in errors:
        field = _field_label(error.get("loc"))
        msg = _clean_message(str(error.get("msg") or "Invalid value."))
        fields.append({"field": field, "message": msg})
    return fields


def install_validation_exception_handlers(app: FastAPI, *, service_slug: str) -> None:
    """Install consistent error responses for all service apps.

    The project has many microservice entry points. Registering this once in the
    app factory guarantees missing/null/invalid values are reported consistently
    across Auth, Order, Inventory, Notification, and legacy compatibility routes.
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        fields = _validation_fields(exc.errors())
        message = "Please correct the highlighted field(s)."
        if len(fields) == 1:
            message = f"{fields[0]['field']}: {fields[0]['message']}"
        elif fields:
            message = "; ".join(f"{item['field']}: {item['message']}" for item in fields[:5])

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": message,
                "fields": fields,
                "service": service_slug,
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            message = detail.get("message") or detail.get("detail") or "Request failed."
        else:
            message = str(detail or "Request failed.")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "REQUEST_ERROR" if exc.status_code < 500 else "SERVER_ERROR",
                "message": message,
                "detail": detail,
                "service": service_slug,
                "path": str(request.url.path),
            },
            headers=getattr(exc, "headers", None),
        )
