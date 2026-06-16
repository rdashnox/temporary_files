from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user, require_permission
from ..schemas.database_entities import PlanningRequestCreate, ReportCreate
from ..services import database_entity_service

router = APIRouter()


@router.get("/me")
async def read_current_database_user(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user with roles and permissions from the database."""
    return current_user


@router.get("/roles")
async def list_roles(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "roles.manage")
    return database_entity_service.list_roles(db)


@router.get("/permissions")
async def list_permissions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "roles.manage")
    return database_entity_service.list_permissions(db)


@router.get("/orders")
async def list_orders(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=25, ge=1, le=100),
):
    require_permission(current_user, "orders.read")
    return database_entity_service.list_orders(db, limit)


@router.get("/reports")
async def list_reports(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=25, ge=1, le=100),
):
    require_permission(current_user, "reports.read")
    return database_entity_service.list_reports(db, limit)


@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def create_report(
    report_create: ReportCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "reports.manage")
    return database_entity_service.create_report(db, report_create, current_user)


@router.get("/planning-requests")
async def list_planning_requests(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=25, ge=1, le=100),
):
    require_permission(current_user, "planning.read")
    return database_entity_service.list_planning_requests(db, limit)


@router.post("/planning-requests", status_code=status.HTTP_201_CREATED)
async def create_planning_request(
    planning_request_create: PlanningRequestCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_permission(current_user, "planning.manage")
    return database_entity_service.create_planning_request(
        db,
        planning_request_create,
        current_user,
    )


@router.get("/audit-logs")
async def list_audit_logs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
):
    require_permission(current_user, "audit.read")
    return database_entity_service.list_audit_logs(db, limit)
