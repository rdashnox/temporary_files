from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

ORDER_STATUSES = {"NEW", "PAID", "PACKED", "SHIPPED", "COMPLETED", "CANCELLED", "EXCEPTION"}
REPORT_STATUSES = {"QUEUED", "RUNNING", "READY", "FAILED"}
PLANNING_STATUSES = {"DRAFT", "SUBMITTED", "APPROVED", "REJECTED", "CANCELLED"}
AUDIT_ACTIONS = {"CREATE", "UPDATE", "DELETE", "LOGIN", "PASSWORD_RESET", "VERIFY_EMAIL", "CHECKOUT"}


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _require_text(value: str | None, field_name: str) -> str:
    cleaned = _clean_optional(value)
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    return cleaned


def _normalize_upper(value: str | None, allowed: set[str], field_name: str, default: str | None = None) -> str | None:
    if value is None:
        return default
    cleaned = str(value).strip().upper()
    if not cleaned:
        return default
    if cleaned not in allowed:
        raise ValueError(f"Invalid {field_name}. Allowed values: {', '.join(sorted(allowed))}.")
    return cleaned


def _validate_unique_product_ids(items: list["OrderItemCreate"] | None) -> None:
    if not items:
        return
    seen: set[int] = set()
    duplicates: set[int] = set()
    for item in items:
        product_id = int(item.product_id)
        if product_id in seen:
            duplicates.add(product_id)
        seen.add(product_id)
    if duplicates:
        raise ValueError(f"Duplicate product_id values are not allowed in one order: {', '.join(map(str, sorted(duplicates)))}.")


class PaginationParams(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    limit: int = Field(default=25, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    search: str | None = Field(default=None, max_length=120)

    @field_validator("search")
    @classmethod
    def clean_search(cls, value: str | None):
        return _clean_optional(value)


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: EmailStr
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    is_active: bool = True
    is_verified: bool = True
    role_ids: list[int] = Field(default_factory=list)

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str | None):
        return _clean_optional(value)

    @field_validator("password")
    @classmethod
    def password_required(cls, value: str):
        return _require_text(value, "Password")

    @field_validator("role_ids")
    @classmethod
    def valid_role_ids(cls, values: list[int]):
        return sorted({int(value) for value in values if int(value) > 0})


class UserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: EmailStr | None = None
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None
    is_verified: bool | None = None
    role_ids: list[int] | None = None

    @field_validator("full_name", "password")
    @classmethod
    def clean_optional_text(cls, value: str | None):
        return _clean_optional(value)

    @field_validator("role_ids")
    @classmethod
    def valid_update_role_ids(cls, values: list[int] | None):
        if values is None:
            return None
        return sorted({int(value) for value in values if int(value) > 0})


class RoleCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    permission_ids: list[int] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def role_name_required(cls, value: str):
        return _require_text(value, "Role name")

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str | None):
        return _clean_optional(value)

    @field_validator("permission_ids")
    @classmethod
    def valid_permission_ids(cls, values: list[int]):
        return sorted({int(value) for value in values if int(value) > 0})


class RoleUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    permission_ids: list[int] | None = None

    @field_validator("name", "description")
    @classmethod
    def clean_role_update_text(cls, value: str | None):
        return _clean_optional(value)

    @field_validator("permission_ids")
    @classmethod
    def valid_update_permission_ids(cls, values: list[int] | None):
        if values is None:
            return None
        return sorted({int(value) for value in values if int(value) > 0})


class PermissionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(..., min_length=3, max_length=120)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    module: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)

    @field_validator("code")
    @classmethod
    def code_required(cls, value: str):
        return _require_text(value, "Permission code").lower().replace(" ", ".")

    @field_validator("name", "module", "description")
    @classmethod
    def clean_permission_text(cls, value: str | None):
        return _clean_optional(value)


class PermissionUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str | None = Field(default=None, min_length=3, max_length=120)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    module: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)

    @field_validator("code")
    @classmethod
    def clean_permission_code(cls, value: str | None):
        cleaned = _clean_optional(value)
        return cleaned.lower().replace(" ", ".") if cleaned else None

    @field_validator("name", "module", "description")
    @classmethod
    def clean_permission_update_text(cls, value: str | None):
        return _clean_optional(value)


class OrderItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: int = Field(..., ge=1)
    product_name: str = Field(..., min_length=2, max_length=120)
    quantity: int = Field(..., ge=1, le=999)
    unit_price: Decimal = Field(..., gt=0)

    @field_validator("product_name")
    @classmethod
    def product_name_required(cls, value: str):
        return _require_text(value, "Product name")


class OrderCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_name: str = Field(..., min_length=2, max_length=120)
    delivery_address: str = Field(..., min_length=5, max_length=255)
    payment_method: str = Field(default="Cash on Delivery", min_length=2, max_length=60)
    status: str = Field(default="NEW", max_length=30)
    discount: Decimal = Field(default=0, ge=0)
    shipping_fee: Decimal = Field(default=0, ge=0)
    tax: Decimal = Field(default=0, ge=0)
    items: list[OrderItemCreate] = Field(..., min_length=1)

    @field_validator("customer_name")
    @classmethod
    def customer_name_required(cls, value: str):
        return _require_text(value, "Customer name")

    @field_validator("delivery_address")
    @classmethod
    def delivery_address_required(cls, value: str):
        return _require_text(value, "Delivery address")

    @field_validator("payment_method")
    @classmethod
    def payment_method_required(cls, value: str):
        return _require_text(value, "Payment method")

    @field_validator("status")
    @classmethod
    def valid_order_status(cls, value: str):
        return _normalize_upper(value, ORDER_STATUSES, "order status", "NEW")

    @model_validator(mode="after")
    def validate_items(self):
        _validate_unique_product_ids(self.items)
        return self


class OrderUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_name: str | None = Field(default=None, min_length=2, max_length=120)
    delivery_address: str | None = Field(default=None, min_length=5, max_length=255)
    payment_method: str | None = Field(default=None, max_length=60)
    status: str | None = Field(default=None, max_length=30)
    discount: Decimal | None = Field(default=None, ge=0)
    shipping_fee: Decimal | None = Field(default=None, ge=0)
    tax: Decimal | None = Field(default=None, ge=0)
    items: list[OrderItemCreate] | None = None

    @field_validator("customer_name", "delivery_address", "payment_method")
    @classmethod
    def clean_order_update_text(cls, value: str | None):
        return _clean_optional(value)

    @field_validator("status")
    @classmethod
    def valid_order_update_status(cls, value: str | None):
        return _normalize_upper(value, ORDER_STATUSES, "order status")

    @field_validator("items")
    @classmethod
    def items_not_empty_when_supplied(cls, value: list[OrderItemCreate] | None):
        if value is not None and len(value) == 0:
            raise ValueError("Order items cannot be empty when supplied.")
        return value

    @model_validator(mode="after")
    def validate_update_payload(self):
        supplied = [name for name, value in self.model_dump().items() if value is not None]
        if not supplied:
            raise ValueError("At least one order field must be provided for update.")
        _validate_unique_product_ids(self.items)
        return self


class ReportCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=3, max_length=160)
    report_type: str = Field(..., min_length=2, max_length=80)
    status: str = Field(default="QUEUED", max_length=30)
    parameters: dict[str, Any] | None = None
    file_path: str | None = Field(default=None, max_length=255)

    @field_validator("name", "report_type")
    @classmethod
    def report_required_text(cls, value: str, info):
        return _require_text(value, info.field_name.replace("_", " ").title())

    @field_validator("status")
    @classmethod
    def valid_report_status(cls, value: str):
        return _normalize_upper(value, REPORT_STATUSES, "report status", "QUEUED")

    @field_validator("file_path")
    @classmethod
    def clean_file_path(cls, value: str | None):
        return _clean_optional(value)


class ReportUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=3, max_length=160)
    report_type: str | None = Field(default=None, min_length=2, max_length=80)
    status: str | None = Field(default=None, max_length=30)
    parameters: dict[str, Any] | None = None
    file_path: str | None = Field(default=None, max_length=255)
    completed_at: datetime | None = None

    @field_validator("name", "report_type", "file_path")
    @classmethod
    def clean_report_update_text(cls, value: str | None):
        return _clean_optional(value)

    @field_validator("status")
    @classmethod
    def valid_report_update_status(cls, value: str | None):
        return _normalize_upper(value, REPORT_STATUSES, "report status")


class PlanningRequestCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    priority: str = Field(default="normal", max_length=30)
    status: str = Field(default="SUBMITTED", max_length=30)
    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def planning_title_required(cls, value: str):
        return _require_text(value, "Title")

    @field_validator("description", "priority")
    @classmethod
    def clean_planning_text(cls, value: str | None):
        return _clean_optional(value)

    @field_validator("status")
    @classmethod
    def valid_planning_status(cls, value: str):
        return _normalize_upper(value, PLANNING_STATUSES, "planning status", "SUBMITTED")


class PlanningRequestUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    priority: str | None = Field(default=None, max_length=30)
    status: str | None = Field(default=None, max_length=30)
    due_date: datetime | None = None

    @field_validator("title", "description", "priority")
    @classmethod
    def clean_planning_update_text(cls, value: str | None):
        return _clean_optional(value)

    @field_validator("status")
    @classmethod
    def valid_planning_update_status(cls, value: str | None):
        return _normalize_upper(value, PLANNING_STATUSES, "planning status")


class AuditLogCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    action: str = Field(..., min_length=3, max_length=50)
    entity_type: str = Field(..., min_length=2, max_length=80)
    entity_id: str | None = Field(default=None, max_length=80)
    detail: str | None = Field(default=None, max_length=2000)
    ip_address: str | None = Field(default=None, max_length=80)
    user_agent: str | None = Field(default=None, max_length=255)

    @field_validator("action")
    @classmethod
    def valid_audit_action(cls, value: str):
        return _normalize_upper(value, AUDIT_ACTIONS, "audit action", "CREATE")

    @field_validator("entity_type")
    @classmethod
    def entity_type_required(cls, value: str):
        return _require_text(value, "Entity type")

    @field_validator("entity_id", "detail", "ip_address", "user_agent")
    @classmethod
    def clean_audit_text(cls, value: str | None):
        return _clean_optional(value)


class AuditLogUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    action: str | None = Field(default=None, min_length=3, max_length=50)
    entity_type: str | None = Field(default=None, min_length=2, max_length=80)
    entity_id: str | None = Field(default=None, max_length=80)
    detail: str | None = Field(default=None, max_length=2000)
    ip_address: str | None = Field(default=None, max_length=80)
    user_agent: str | None = Field(default=None, max_length=255)

    @field_validator("action")
    @classmethod
    def valid_audit_update_action(cls, value: str | None):
        return _normalize_upper(value, AUDIT_ACTIONS, "audit action")

    @field_validator("entity_type", "entity_id", "detail", "ip_address", "user_agent")
    @classmethod
    def clean_audit_update_text(cls, value: str | None):
        return _clean_optional(value)
