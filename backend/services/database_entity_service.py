import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.security import hash_password, validate_password_strength
from ..models import (
    AuditAction,
    AuditLog,
    Order,
    OrderItem,
    OrderStatus,
    Permission,
    PlanningRequest,
    PlanningRequestStatus,
    Report,
    ReportStatus,
    Role,
    User,
)
from ..schemas.database_entities import (
    AuditLogCreate,
    AuditLogUpdate,
    OrderCreate,
    OrderItemCreate,
    OrderUpdate,
    PermissionCreate,
    PermissionUpdate,
    PlanningRequestCreate,
    PlanningRequestUpdate,
    ReportCreate,
    ReportUpdate,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)
from .audit_service import create_audit_log


class EntityNotFound(HTTPException):
    def __init__(self, entity: str, entity_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity} with id {entity_id} was not found.",
        )


def _normalized(value: str) -> str:
    return value.strip().lower()


def _humanize_permission_code(code: str) -> str:
    return code.replace('.', ' ').replace('_', ' ').title()


def _permission_module_from_code(code: str) -> str:
    return code.split('.', 1)[0] if '.' in code else code


def _enum_from_input(enum_cls, value: str | None, default=None):
    if value is None:
        return default
    cleaned = value.strip()
    if not cleaned:
        return default
    upper_value = cleaned.upper()
    lower_value = cleaned.lower()
    if upper_value in enum_cls.__members__:
        return enum_cls[upper_value]
    for member in enum_cls:
        if member.value.lower() == lower_value:
            return member
    allowed = ", ".join(member.name for member in enum_cls)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid status/action '{value}'. Allowed values: {allowed}.",
    )


def _enum_to_api(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "name"):
        return value.name
    return str(value).upper()


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def money(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def _actor(db: Session, current_user: dict | None) -> User | None:
    if not current_user or not current_user.get("id"):
        return None
    return db.get(User, current_user["id"])


def _commit_or_integrity_error(db: Session, message: str):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message) from exc


def _validate_password(password: str):
    errors = validate_password_strength(password)
    if errors:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=" ".join(errors))


def _roles_by_ids(db: Session, role_ids: list[int]) -> list[Role]:
    if not role_ids:
        return []
    roles = db.scalars(select(Role).where(Role.id.in_(role_ids))).all()
    if len(roles) != len(set(role_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more role IDs are invalid.")
    return list(roles)


def _permissions_by_ids(db: Session, permission_ids: list[int]) -> list[Permission]:
    if not permission_ids:
        return []
    permissions = db.scalars(select(Permission).where(Permission.id.in_(permission_ids))).all()
    if len(permissions) != len(set(permission_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more permission IDs are invalid.")
    return list(permissions)


# ----- Serializers -----
def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "last_login_at": _iso(user.last_login_at),
        "created_at": _iso(user.created_at),
        "updated_at": _iso(user.updated_at),
        "roles": [{"id": role.id, "name": role.name} for role in user.roles],
        "role_ids": [role.id for role in user.roles],
        "permissions": sorted({permission.code for role in user.roles if role.is_active for permission in role.permissions}),
    }


def role_to_dict(role: Role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active,
        "created_at": _iso(role.created_at),
        "updated_at": _iso(role.updated_at),
        "permissions": [permission.code for permission in role.permissions],
        "permission_ids": [permission.id for permission in role.permissions],
        "user_count": len(role.users),
    }


def permission_to_dict(permission: Permission) -> dict:
    return {
        "id": permission.id,
        "code": permission.code,
        "name": permission.name,
        "module": permission.module,
        "description": permission.description,
        "created_at": _iso(permission.created_at),
    }


def order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "user_id": order.user_id,
        "customer_name": order.customer_name,
        "delivery_address": order.delivery_address,
        "payment_method": order.payment_method,
        "status": _enum_to_api(order.status),
        "subtotal": money(order.subtotal),
        "discount": money(order.discount),
        "shipping_fee": money(order.shipping_fee),
        "tax": money(order.tax),
        "total": money(order.total),
        "created_at": _iso(order.created_at),
        "updated_at": _iso(order.updated_at),
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": money(item.unit_price),
                "line_total": money(item.line_total),
            }
            for item in order.items
        ],
    }


def report_to_dict(report: Report) -> dict:
    parameters = None
    if report.parameters_json:
        try:
            parameters = json.loads(report.parameters_json)
        except json.JSONDecodeError:
            parameters = {"raw": report.parameters_json}
    return {
        "id": report.id,
        "name": report.name,
        "report_type": report.report_type,
        "status": _enum_to_api(report.status),
        "parameters": parameters,
        "parameters_json": report.parameters_json,
        "file_path": report.file_path,
        "created_by_user_id": report.created_by_user_id,
        "created_at": _iso(report.created_at),
        "completed_at": _iso(report.completed_at),
    }


def planning_request_to_dict(request: PlanningRequest) -> dict:
    return {
        "id": request.id,
        "request_number": request.request_number,
        "title": request.title,
        "description": request.description,
        "priority": request.priority,
        "status": _enum_to_api(request.status),
        "requested_by_user_id": request.requested_by_user_id,
        "due_date": _iso(request.due_date),
        "created_at": _iso(request.created_at),
        "updated_at": _iso(request.updated_at),
    }


def audit_log_to_dict(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "actor_user_id": log.actor_user_id,
        "actor_username": log.actor.username if log.actor else None,
        "action": _enum_to_api(log.action),
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "detail": log.detail,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "created_at": _iso(log.created_at),
    }


# ----- Utility -----
def _paginate(statement, limit: int, offset: int):
    return statement.offset(offset).limit(limit)


def _recalculate_order_totals(order: Order):
    subtotal = sum((item.line_total for item in order.items), Decimal("0.00"))
    order.subtotal = subtotal
    order.total = max(subtotal - order.discount, Decimal("0.00")) + order.shipping_fee + order.tax


def _replace_order_items(db: Session, order: Order, items: list[OrderItemCreate]):
    order.items.clear()
    db.flush()
    for payload in items:
        line_total = Decimal(payload.quantity) * payload.unit_price
        order.items.append(
            OrderItem(
                product_id=payload.product_id,
                product_name=payload.product_name,
                quantity=payload.quantity,
                unit_price=payload.unit_price,
                line_total=line_total,
            )
        )
    _recalculate_order_totals(order)




def get_dashboard_summary_counts(db: Session) -> dict[str, int]:
    """Return true database row counts for Admin Dashboard KPI cards.

    These counts intentionally do not use pagination, so the frontend can show
    the real number of records stored in MySQL instead of the number currently
    loaded in a table page.
    """
    return {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "orders": db.scalar(select(func.count()).select_from(Order)) or 0,
        "reports": db.scalar(select(func.count()).select_from(Report)) or 0,
        "audit-logs": db.scalar(select(func.count()).select_from(AuditLog)) or 0,
        "roles": db.scalar(select(func.count()).select_from(Role)) or 0,
        "permissions": db.scalar(select(func.count()).select_from(Permission)) or 0,
        "planning-requests": db.scalar(select(func.count()).select_from(PlanningRequest)) or 0,
    }

# ----- Users -----
def list_users(db: Session, limit: int = 25, offset: int = 0, search: str | None = None) -> list[dict]:
    statement = select(User).order_by(desc(User.created_at))
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(User.username.ilike(term), User.email.ilike(term), User.full_name.ilike(term)))
    users = db.scalars(_paginate(statement, limit, offset)).all()
    return [user_to_dict(user) for user in users]


def get_user(db: Session, user_id: int) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise EntityNotFound("User", user_id)
    return user_to_dict(user)


def create_user(db: Session, user_create: UserCreate, current_user: dict) -> dict:
    username = _normalized(user_create.username)
    email = _normalized(user_create.email or user_create.username)
    _validate_password(user_create.password)
    user = User(
        username=username,
        email=email,
        full_name=user_create.full_name,
        hashed_password=hash_password(user_create.password),
        is_active=user_create.is_active,
        is_verified=user_create.is_verified,
        roles=_roles_by_ids(db, user_create.role_ids),
    )
    db.add(user)
    db.flush()
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.CREATE, entity_type="users", entity_id=str(user.id), detail=f"Created user {user.email}.")
    _commit_or_integrity_error(db, "A user with this username or email already exists.")
    db.refresh(user)
    return user_to_dict(user)


def update_user(db: Session, user_id: int, user_update: UserUpdate, current_user: dict) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise EntityNotFound("User", user_id)
    if user_update.username is not None:
        user.username = _normalized(user_update.username)
    if user_update.email is not None:
        user.email = _normalized(user_update.email)
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.password:
        _validate_password(user_update.password)
        user.hashed_password = hash_password(user_update.password)
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.is_verified is not None:
        user.is_verified = user_update.is_verified
    if user_update.role_ids is not None:
        user.roles = _roles_by_ids(db, user_update.role_ids)
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.UPDATE, entity_type="users", entity_id=str(user.id), detail=f"Updated user {user.email}.")
    _commit_or_integrity_error(db, "A user with this username or email already exists.")
    db.refresh(user)
    return user_to_dict(user)


def delete_user(db: Session, user_id: int, current_user: dict) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise EntityNotFound("User", user_id)
    if current_user.get("id") == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own account while logged in.")
    user.is_active = False
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.DELETE, entity_type="users", entity_id=str(user.id), detail=f"Deactivated user {user.email}.")
    db.commit()
    return {"message": "User deactivated successfully.", "id": user_id}


# ----- Roles -----
def list_roles(db: Session, limit: int = 100, offset: int = 0, search: str | None = None) -> list[dict]:
    statement = select(Role).order_by(Role.name)
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(Role.name.ilike(term), Role.description.ilike(term)))
    roles = db.scalars(_paginate(statement, limit, offset)).all()
    return [role_to_dict(role) for role in roles]


def get_role(db: Session, role_id: int) -> dict:
    role = db.get(Role, role_id)
    if role is None:
        raise EntityNotFound("Role", role_id)
    return role_to_dict(role)


def create_role(db: Session, role_create: RoleCreate, current_user: dict) -> dict:
    role = Role(name=role_create.name.strip(), description=role_create.description, is_active=role_create.is_active)
    role.permissions = _permissions_by_ids(db, role_create.permission_ids)
    db.add(role)
    db.flush()
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.CREATE, entity_type="roles", entity_id=str(role.id), detail=f"Created role {role.name}.")
    _commit_or_integrity_error(db, "A role with this name already exists.")
    db.refresh(role)
    return role_to_dict(role)


def update_role(db: Session, role_id: int, role_update: RoleUpdate, current_user: dict) -> dict:
    role = db.get(Role, role_id)
    if role is None:
        raise EntityNotFound("Role", role_id)
    if role_update.name is not None:
        role.name = role_update.name.strip()
    if role_update.description is not None:
        role.description = role_update.description
    if role_update.is_active is not None:
        role.is_active = role_update.is_active
    if role_update.permission_ids is not None:
        role.permissions = _permissions_by_ids(db, role_update.permission_ids)
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.UPDATE, entity_type="roles", entity_id=str(role.id), detail=f"Updated role {role.name}.")
    _commit_or_integrity_error(db, "A role with this name already exists.")
    db.refresh(role)
    return role_to_dict(role)


def delete_role(db: Session, role_id: int, current_user: dict) -> dict:
    role = db.get(Role, role_id)
    if role is None:
        raise EntityNotFound("Role", role_id)
    if role.name in {"Admin", "Manager", "Staff"}:
        role.is_active = False
        detail = f"Deactivated protected default role {role.name}."
    else:
        detail = f"Deleted role {role.name}."
        db.delete(role)
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.DELETE, entity_type="roles", entity_id=str(role_id), detail=detail)
    db.commit()
    return {"message": detail, "id": role_id}


# ----- Permissions -----
def list_permissions(db: Session, limit: int = 200, offset: int = 0, search: str | None = None) -> list[dict]:
    statement = select(Permission).order_by(Permission.module, Permission.code)
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(Permission.code.ilike(term), Permission.name.ilike(term), Permission.module.ilike(term)))
    permissions = db.scalars(_paginate(statement, limit, offset)).all()
    return [permission_to_dict(permission) for permission in permissions]


def get_permission(db: Session, permission_id: int) -> dict:
    permission = db.get(Permission, permission_id)
    if permission is None:
        raise EntityNotFound("Permission", permission_id)
    return permission_to_dict(permission)


def create_permission(db: Session, permission_create: PermissionCreate, current_user: dict) -> dict:
    code = permission_create.code.strip().lower().replace(' ', '.')
    name = (permission_create.name or _humanize_permission_code(code)).strip()
    module = (permission_create.module or _permission_module_from_code(code)).strip().lower()
    permission = Permission(
        code=code,
        name=name,
        module=module,
        description=permission_create.description,
    )
    db.add(permission)
    db.flush()
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.CREATE, entity_type="permissions", entity_id=str(permission.id), detail=f"Created permission {permission.code}.")
    _commit_or_integrity_error(db, "A permission with this code already exists.")
    db.refresh(permission)
    return permission_to_dict(permission)


def update_permission(db: Session, permission_id: int, permission_update: PermissionUpdate, current_user: dict) -> dict:
    permission = db.get(Permission, permission_id)
    if permission is None:
        raise EntityNotFound("Permission", permission_id)
    if permission_update.code is not None:
        permission.code = permission_update.code.strip().lower().replace(' ', '.')
    if permission_update.name is not None:
        permission.name = permission_update.name.strip() or _humanize_permission_code(permission.code)
    if permission_update.module is not None:
        permission.module = permission_update.module.strip().lower() or _permission_module_from_code(permission.code)
    if permission_update.description is not None:
        permission.description = permission_update.description
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.UPDATE, entity_type="permissions", entity_id=str(permission.id), detail=f"Updated permission {permission.code}.")
    _commit_or_integrity_error(db, "A permission with this code already exists.")
    db.refresh(permission)
    return permission_to_dict(permission)


def delete_permission(db: Session, permission_id: int, current_user: dict) -> dict:
    permission = db.get(Permission, permission_id)
    if permission is None:
        raise EntityNotFound("Permission", permission_id)
    detail = f"Deleted permission {permission.code}."
    db.delete(permission)
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.DELETE, entity_type="permissions", entity_id=str(permission_id), detail=detail)
    db.commit()
    return {"message": detail, "id": permission_id}


# ----- Orders -----
def list_orders(db: Session, limit: int = 25, offset: int = 0, search: str | None = None) -> list[dict]:
    statement = select(Order).order_by(desc(Order.created_at))
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(Order.order_number.ilike(term), Order.customer_name.ilike(term), Order.status.ilike(term)))
    orders = db.scalars(_paginate(statement, limit, offset)).all()
    return [order_to_dict(order) for order in orders]


def get_order(db: Session, order_id: int) -> dict:
    order = db.get(Order, order_id)
    if order is None:
        raise EntityNotFound("Order", order_id)
    return order_to_dict(order)


def create_order(db: Session, order_create: OrderCreate, current_user: dict) -> dict:
    order = Order(
        order_number=f"FM-{uuid4().hex[:8].upper()}",
        user_id=current_user.get("id"),
        customer_name=order_create.customer_name,
        delivery_address=order_create.delivery_address,
        payment_method=order_create.payment_method,
        status=_enum_from_input(OrderStatus, order_create.status, OrderStatus.NEW),
        discount=order_create.discount,
        shipping_fee=order_create.shipping_fee,
        tax=order_create.tax,
        subtotal=Decimal("0.00"),
        total=Decimal("0.00"),
    )
    db.add(order)
    db.flush()
    _replace_order_items(db, order, order_create.items)
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.CREATE, entity_type="orders", entity_id=order.order_number, detail=f"Created order for {order.customer_name}.")
    db.commit()
    db.refresh(order)
    return order_to_dict(order)


def update_order(db: Session, order_id: int, order_update: OrderUpdate, current_user: dict) -> dict:
    order = db.get(Order, order_id)
    if order is None:
        raise EntityNotFound("Order", order_id)
    for field in ["customer_name", "delivery_address", "payment_method", "discount", "shipping_fee", "tax"]:
        value = getattr(order_update, field)
        if value is not None:
            setattr(order, field, value)
    if order_update.status is not None:
        order.status = _enum_from_input(OrderStatus, order_update.status, order.status)
    if order_update.items is not None:
        _replace_order_items(db, order, order_update.items)
    else:
        _recalculate_order_totals(order)
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.UPDATE, entity_type="orders", entity_id=order.order_number, detail=f"Updated order {order.order_number}.")
    db.commit()
    db.refresh(order)
    return order_to_dict(order)


def delete_order(db: Session, order_id: int, current_user: dict) -> dict:
    order = db.get(Order, order_id)
    if order is None:
        raise EntityNotFound("Order", order_id)
    order_number = order.order_number
    db.delete(order)
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.DELETE, entity_type="orders", entity_id=order_number, detail=f"Deleted order {order_number}.")
    db.commit()
    return {"message": "Order deleted successfully.", "id": order_id}


# ----- Reports -----
def list_reports(db: Session, limit: int = 25, offset: int = 0, search: str | None = None) -> list[dict]:
    statement = select(Report).order_by(desc(Report.created_at))
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(Report.name.ilike(term), Report.report_type.ilike(term), Report.status.ilike(term)))
    reports = db.scalars(_paginate(statement, limit, offset)).all()
    return [report_to_dict(report) for report in reports]


def get_report(db: Session, report_id: int) -> dict:
    report = db.get(Report, report_id)
    if report is None:
        raise EntityNotFound("Report", report_id)
    return report_to_dict(report)


def create_report(db: Session, report_create: ReportCreate, current_user: dict) -> dict:
    report = Report(
        name=report_create.name,
        report_type=report_create.report_type,
        status=_enum_from_input(ReportStatus, report_create.status, ReportStatus.QUEUED),
        parameters_json=json.dumps(report_create.parameters or {}),
        file_path=report_create.file_path,
        created_by_user_id=current_user.get("id"),
        completed_at=datetime.now(timezone.utc) if _enum_from_input(ReportStatus, report_create.status, ReportStatus.QUEUED) == ReportStatus.READY else None,
    )
    db.add(report)
    db.flush()
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.CREATE, entity_type="reports", entity_id=str(report.id), detail=f"Created report {report.name}.")
    db.commit()
    db.refresh(report)
    return report_to_dict(report)


def update_report(db: Session, report_id: int, report_update: ReportUpdate, current_user: dict) -> dict:
    report = db.get(Report, report_id)
    if report is None:
        raise EntityNotFound("Report", report_id)
    if report_update.name is not None:
        report.name = report_update.name
    if report_update.report_type is not None:
        report.report_type = report_update.report_type
    if report_update.status is not None:
        report.status = _enum_from_input(ReportStatus, report_update.status, report.status)
    if report_update.parameters is not None:
        report.parameters_json = json.dumps(report_update.parameters)
    if report_update.file_path is not None:
        report.file_path = report_update.file_path
    if report_update.completed_at is not None:
        report.completed_at = report_update.completed_at
    if report.status == ReportStatus.READY and report.completed_at is None:
        report.completed_at = datetime.now(timezone.utc)
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.UPDATE, entity_type="reports", entity_id=str(report.id), detail=f"Updated report {report.name}.")
    db.commit()
    db.refresh(report)
    return report_to_dict(report)


def delete_report(db: Session, report_id: int, current_user: dict) -> dict:
    report = db.get(Report, report_id)
    if report is None:
        raise EntityNotFound("Report", report_id)
    detail = f"Deleted report {report.name}."
    db.delete(report)
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.DELETE, entity_type="reports", entity_id=str(report_id), detail=detail)
    db.commit()
    return {"message": detail, "id": report_id}


# ----- Planning Requests -----
def list_planning_requests(db: Session, limit: int = 25, offset: int = 0, search: str | None = None) -> list[dict]:
    statement = select(PlanningRequest).order_by(desc(PlanningRequest.created_at))
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(PlanningRequest.request_number.ilike(term), PlanningRequest.title.ilike(term), PlanningRequest.priority.ilike(term), PlanningRequest.status.ilike(term)))
    requests = db.scalars(_paginate(statement, limit, offset)).all()
    return [planning_request_to_dict(request) for request in requests]


def get_planning_request(db: Session, planning_request_id: int) -> dict:
    planning_request = db.get(PlanningRequest, planning_request_id)
    if planning_request is None:
        raise EntityNotFound("Planning request", planning_request_id)
    return planning_request_to_dict(planning_request)


def create_planning_request(db: Session, planning_request_create: PlanningRequestCreate, current_user: dict) -> dict:
    planning_request = PlanningRequest(
        request_number=f"PR-{uuid4().hex[:8].upper()}",
        title=planning_request_create.title,
        description=planning_request_create.description,
        priority=planning_request_create.priority,
        status=_enum_from_input(PlanningRequestStatus, planning_request_create.status, PlanningRequestStatus.SUBMITTED),
        requested_by_user_id=current_user.get("id"),
        due_date=planning_request_create.due_date,
    )
    db.add(planning_request)
    db.flush()
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.CREATE, entity_type="planning_requests", entity_id=planning_request.request_number, detail=f"Created planning request {planning_request.title}.")
    db.commit()
    db.refresh(planning_request)
    return planning_request_to_dict(planning_request)


def update_planning_request(db: Session, planning_request_id: int, planning_request_update: PlanningRequestUpdate, current_user: dict) -> dict:
    planning_request = db.get(PlanningRequest, planning_request_id)
    if planning_request is None:
        raise EntityNotFound("Planning request", planning_request_id)
    if planning_request_update.title is not None:
        planning_request.title = planning_request_update.title
    if planning_request_update.description is not None:
        planning_request.description = planning_request_update.description
    if planning_request_update.priority is not None:
        planning_request.priority = planning_request_update.priority
    if planning_request_update.status is not None:
        planning_request.status = _enum_from_input(PlanningRequestStatus, planning_request_update.status, planning_request.status)
    if planning_request_update.due_date is not None:
        planning_request.due_date = planning_request_update.due_date
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.UPDATE, entity_type="planning_requests", entity_id=planning_request.request_number, detail=f"Updated planning request {planning_request.request_number}.")
    db.commit()
    db.refresh(planning_request)
    return planning_request_to_dict(planning_request)


def delete_planning_request(db: Session, planning_request_id: int, current_user: dict) -> dict:
    planning_request = db.get(PlanningRequest, planning_request_id)
    if planning_request is None:
        raise EntityNotFound("Planning request", planning_request_id)
    request_number = planning_request.request_number
    db.delete(planning_request)
    create_audit_log(db, actor=_actor(db, current_user), action=AuditAction.DELETE, entity_type="planning_requests", entity_id=request_number, detail=f"Deleted planning request {request_number}.")
    db.commit()
    return {"message": "Planning request deleted successfully.", "id": planning_request_id}


# ----- Audit Logs -----
def list_audit_logs(db: Session, limit: int = 50, offset: int = 0, search: str | None = None) -> list[dict]:
    statement = select(AuditLog).order_by(desc(AuditLog.created_at))
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(AuditLog.entity_type.ilike(term), AuditLog.entity_id.ilike(term), AuditLog.detail.ilike(term), AuditLog.action.ilike(term)))
    logs = db.scalars(_paginate(statement, limit, offset)).all()
    return [audit_log_to_dict(log) for log in logs]


def get_audit_log(db: Session, audit_log_id: int) -> dict:
    log = db.get(AuditLog, audit_log_id)
    if log is None:
        raise EntityNotFound("Audit log", audit_log_id)
    return audit_log_to_dict(log)


def create_manual_audit_log(db: Session, audit_log_create: AuditLogCreate, current_user: dict) -> dict:
    action = _enum_from_input(AuditAction, audit_log_create.action, AuditAction.CREATE)
    log = AuditLog(
        actor_user_id=current_user.get("id"),
        action=action,
        entity_type=audit_log_create.entity_type,
        entity_id=audit_log_create.entity_id,
        detail=audit_log_create.detail,
        ip_address=audit_log_create.ip_address,
        user_agent=audit_log_create.user_agent,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return audit_log_to_dict(log)


def update_audit_log(db: Session, audit_log_id: int, audit_log_update: AuditLogUpdate, current_user: dict) -> dict:
    log = db.get(AuditLog, audit_log_id)
    if log is None:
        raise EntityNotFound("Audit log", audit_log_id)
    if audit_log_update.action is not None:
        log.action = _enum_from_input(AuditAction, audit_log_update.action, log.action)
    if audit_log_update.entity_type is not None:
        log.entity_type = audit_log_update.entity_type
    if audit_log_update.entity_id is not None:
        log.entity_id = audit_log_update.entity_id
    if audit_log_update.detail is not None:
        log.detail = audit_log_update.detail
    if audit_log_update.ip_address is not None:
        log.ip_address = audit_log_update.ip_address
    if audit_log_update.user_agent is not None:
        log.user_agent = audit_log_update.user_agent
    db.commit()
    db.refresh(log)
    return audit_log_to_dict(log)


def delete_audit_log(db: Session, audit_log_id: int, current_user: dict) -> dict:
    log = db.get(AuditLog, audit_log_id)
    if log is None:
        raise EntityNotFound("Audit log", audit_log_id)
    db.delete(log)
    db.commit()
    return {"message": "Audit log deleted successfully.", "id": audit_log_id}
