from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class PaginationParams(BaseModel):
    limit: int = Field(default=25, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    search: str | None = Field(default=None, max_length=120)


class UserCreate(BaseModel):
    username: EmailStr
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    is_active: bool = True
    is_verified: bool = True
    role_ids: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    username: EmailStr | None = None
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None
    is_verified: bool | None = None
    role_ids: list[int] | None = None


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    permission_ids: list[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    permission_ids: list[int] | None = None


class PermissionCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=120)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    module: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)


class PermissionUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=3, max_length=120)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    module: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)


class OrderItemCreate(BaseModel):
    product_id: int = Field(..., ge=1)
    product_name: str = Field(..., min_length=2, max_length=120)
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., ge=0)


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=120)
    delivery_address: str = Field(..., min_length=5, max_length=255)
    payment_method: str = Field(default="Cash on Delivery", max_length=60)
    status: str = Field(default="NEW", max_length=30)
    discount: Decimal = Field(default=0, ge=0)
    shipping_fee: Decimal = Field(default=0, ge=0)
    tax: Decimal = Field(default=0, ge=0)
    items: list[OrderItemCreate] = Field(default_factory=list)


class OrderUpdate(BaseModel):
    customer_name: str | None = Field(default=None, min_length=2, max_length=120)
    delivery_address: str | None = Field(default=None, min_length=5, max_length=255)
    payment_method: str | None = Field(default=None, max_length=60)
    status: str | None = Field(default=None, max_length=30)
    discount: Decimal | None = Field(default=None, ge=0)
    shipping_fee: Decimal | None = Field(default=None, ge=0)
    tax: Decimal | None = Field(default=None, ge=0)
    items: list[OrderItemCreate] | None = None


class ReportCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=160)
    report_type: str = Field(..., min_length=2, max_length=80)
    status: str = Field(default="QUEUED", max_length=30)
    parameters: dict[str, Any] | None = None
    file_path: str | None = Field(default=None, max_length=255)


class ReportUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=160)
    report_type: str | None = Field(default=None, min_length=2, max_length=80)
    status: str | None = Field(default=None, max_length=30)
    parameters: dict[str, Any] | None = None
    file_path: str | None = Field(default=None, max_length=255)
    completed_at: datetime | None = None


class PlanningRequestCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    priority: str = Field(default="normal", max_length=30)
    status: str = Field(default="SUBMITTED", max_length=30)
    due_date: datetime | None = None


class PlanningRequestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    priority: str | None = Field(default=None, max_length=30)
    status: str | None = Field(default=None, max_length=30)
    due_date: datetime | None = None


class AuditLogCreate(BaseModel):
    action: str = Field(..., min_length=3, max_length=50)
    entity_type: str = Field(..., min_length=2, max_length=80)
    entity_id: str | None = Field(default=None, max_length=80)
    detail: str | None = Field(default=None, max_length=2000)
    ip_address: str | None = Field(default=None, max_length=80)
    user_agent: str | None = Field(default=None, max_length=255)


class AuditLogUpdate(BaseModel):
    action: str | None = Field(default=None, min_length=3, max_length=50)
    entity_type: str | None = Field(default=None, min_length=2, max_length=80)
    entity_id: str | None = Field(default=None, max_length=80)
    detail: str | None = Field(default=None, max_length=2000)
    ip_address: str | None = Field(default=None, max_length=80)
    user_agent: str | None = Field(default=None, max_length=255)
