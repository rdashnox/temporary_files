from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user, require_permission, user_has_permission
from ..schemas.database_entities import (
    AuditLogCreate,
    AuditLogUpdate,
    OrderCreate,
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
from ..services import database_entity_service

router = APIRouter()


def pagination(
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=120),
):
    return {"limit": limit, "offset": offset, "search": search}


@router.get("/me")
async def read_current_database_user(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user with roles and permissions from the database."""
    return current_user




@router.get("/summary")
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return true database counts for Admin Dashboard KPI cards."""
    all_counts = database_entity_service.get_dashboard_summary_counts(db)
    permission_map = {
        "users": "users.read",
        "orders": "orders.read",
        "reports": "reports.read",
        "audit-logs": "audit.read",
        "roles": "roles.read",
        "permissions": "permissions.read",
        "planning-requests": "planning.read",
    }
    return {
        entity: count
        for entity, count in all_counts.items()
        if user_has_permission(current_user, permission_map[entity])
    }


# ----- Users -----
@router.get("/users")
async def list_users(
    page: dict = Depends(pagination),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "users.read")
    return database_entity_service.list_users(db, **page)


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "users.manage")
    return database_entity_service.create_user(db, user_create, current_user)


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "users.read")
    return database_entity_service.get_user(db, user_id)


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "users.manage")
    return database_entity_service.update_user(db, user_id, user_update, current_user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "users.manage")
    return database_entity_service.delete_user(db, user_id, current_user)


# ----- Roles -----
@router.get("/roles")
async def list_roles(
    page: dict = Depends(pagination),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "roles.read")
    return database_entity_service.list_roles(db, **page)


@router.post("/roles", status_code=status.HTTP_201_CREATED)
async def create_role(
    role_create: RoleCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "roles.manage")
    return database_entity_service.create_role(db, role_create, current_user)


@router.get("/roles/{role_id}")
async def get_role(
    role_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "roles.read")
    return database_entity_service.get_role(db, role_id)


@router.put("/roles/{role_id}")
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "roles.manage")
    return database_entity_service.update_role(db, role_id, role_update, current_user)


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "roles.manage")
    return database_entity_service.delete_role(db, role_id, current_user)


# ----- Permissions -----
@router.get("/permissions")
async def list_permissions(
    page: dict = Depends(pagination),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "permissions.read")
    return database_entity_service.list_permissions(db, **page)


@router.post("/permissions", status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_create: PermissionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "permissions.manage")
    return database_entity_service.create_permission(db, permission_create, current_user)


@router.get("/permissions/{permission_id}")
async def get_permission(
    permission_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "permissions.read")
    return database_entity_service.get_permission(db, permission_id)


@router.put("/permissions/{permission_id}")
async def update_permission(
    permission_id: int,
    permission_update: PermissionUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "permissions.manage")
    return database_entity_service.update_permission(db, permission_id, permission_update, current_user)


@router.delete("/permissions/{permission_id}")
async def delete_permission(
    permission_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "permissions.manage")
    return database_entity_service.delete_permission(db, permission_id, current_user)


# ----- Orders -----
@router.get("/orders")
async def list_orders(
    page: dict = Depends(pagination),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "orders.read")
    return database_entity_service.list_orders(db, **page)


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(
    order_create: OrderCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "orders.manage")
    return database_entity_service.create_order(db, order_create, current_user)


@router.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "orders.read")
    return database_entity_service.get_order(db, order_id)


@router.put("/orders/{order_id}")
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "orders.manage")
    return database_entity_service.update_order(db, order_id, order_update, current_user)


@router.delete("/orders/{order_id}")
async def delete_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "orders.manage")
    return database_entity_service.delete_order(db, order_id, current_user)


# ----- Reports -----
@router.get("/reports")
async def list_reports(
    page: dict = Depends(pagination),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "reports.read")
    return database_entity_service.list_reports(db, **page)


@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def create_report(
    report_create: ReportCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "reports.manage")
    return database_entity_service.create_report(db, report_create, current_user)


@router.get("/reports/{report_id}")
async def get_report(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "reports.read")
    return database_entity_service.get_report(db, report_id)


@router.put("/reports/{report_id}")
async def update_report(
    report_id: int,
    report_update: ReportUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "reports.manage")
    return database_entity_service.update_report(db, report_id, report_update, current_user)


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "reports.manage")
    return database_entity_service.delete_report(db, report_id, current_user)


# ----- Planning Requests -----
@router.get("/planning-requests")
async def list_planning_requests(
    page: dict = Depends(pagination),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "planning.read")
    return database_entity_service.list_planning_requests(db, **page)


@router.post("/planning-requests", status_code=status.HTTP_201_CREATED)
async def create_planning_request(
    planning_request_create: PlanningRequestCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "planning.manage")
    return database_entity_service.create_planning_request(db, planning_request_create, current_user)


@router.get("/planning-requests/{planning_request_id}")
async def get_planning_request(
    planning_request_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "planning.read")
    return database_entity_service.get_planning_request(db, planning_request_id)


@router.put("/planning-requests/{planning_request_id}")
async def update_planning_request(
    planning_request_id: int,
    planning_request_update: PlanningRequestUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "planning.manage")
    return database_entity_service.update_planning_request(db, planning_request_id, planning_request_update, current_user)


@router.delete("/planning-requests/{planning_request_id}")
async def delete_planning_request(
    planning_request_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "planning.manage")
    return database_entity_service.delete_planning_request(db, planning_request_id, current_user)


# ----- Audit Logs -----
@router.get("/audit-logs")
async def list_audit_logs(
    page: dict = Depends(pagination),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "audit.read")
    return database_entity_service.list_audit_logs(db, **page)


@router.post("/audit-logs", status_code=status.HTTP_201_CREATED)
async def create_manual_audit_log(
    audit_log_create: AuditLogCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "audit.manage")
    return database_entity_service.create_manual_audit_log(db, audit_log_create, current_user)


@router.get("/audit-logs/{audit_log_id}")
async def get_audit_log(
    audit_log_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "audit.read")
    return database_entity_service.get_audit_log(db, audit_log_id)


@router.put("/audit-logs/{audit_log_id}")
async def update_audit_log(
    audit_log_id: int,
    audit_log_update: AuditLogUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "audit.manage")
    return database_entity_service.update_audit_log(db, audit_log_id, audit_log_update, current_user)


@router.delete("/audit-logs/{audit_log_id}")
async def delete_audit_log(
    audit_log_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "audit.manage")
    return database_entity_service.delete_audit_log(db, audit_log_id, current_user)
