import json
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..models import (
    AuditAction,
    AuditLog,
    Order,
    Permission,
    PlanningRequest,
    PlanningRequestStatus,
    Report,
    ReportStatus,
    Role,
)
from ..schemas.database_entities import PlanningRequestCreate, ReportCreate
from .audit_service import create_audit_log


def money(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def role_to_dict(role: Role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active,
        "permissions": [permission.code for permission in role.permissions],
    }


def permission_to_dict(permission: Permission) -> dict:
    return {
        "id": permission.id,
        "code": permission.code,
        "name": permission.name,
        "module": permission.module,
        "description": permission.description,
    }


def order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_name": order.customer_name,
        "payment_method": order.payment_method,
        "status": order.status.value,
        "subtotal": money(order.subtotal),
        "discount": money(order.discount),
        "shipping_fee": money(order.shipping_fee),
        "tax": money(order.tax),
        "total": money(order.total),
        "created_at": order.created_at.isoformat(),
        "items": [
            {
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
    return {
        "id": report.id,
        "name": report.name,
        "report_type": report.report_type,
        "status": report.status.value,
        "parameters": json.loads(report.parameters_json) if report.parameters_json else None,
        "file_path": report.file_path,
        "created_at": report.created_at.isoformat(),
        "completed_at": report.completed_at.isoformat() if report.completed_at else None,
    }


def planning_request_to_dict(request: PlanningRequest) -> dict:
    return {
        "id": request.id,
        "request_number": request.request_number,
        "title": request.title,
        "description": request.description,
        "priority": request.priority,
        "status": request.status.value,
        "due_date": request.due_date.isoformat() if request.due_date else None,
        "created_at": request.created_at.isoformat(),
        "updated_at": request.updated_at.isoformat(),
    }


def audit_log_to_dict(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "actor_user_id": log.actor_user_id,
        "action": log.action.value,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "detail": log.detail,
        "ip_address": log.ip_address,
        "created_at": log.created_at.isoformat(),
    }


def list_roles(db: Session) -> list[dict]:
    roles = db.scalars(select(Role).order_by(Role.name)).all()
    return [role_to_dict(role) for role in roles]


def list_permissions(db: Session) -> list[dict]:
    permissions = db.scalars(select(Permission).order_by(Permission.module, Permission.code)).all()
    return [permission_to_dict(permission) for permission in permissions]


def list_orders(db: Session, limit: int = 25) -> list[dict]:
    orders = db.scalars(select(Order).order_by(desc(Order.created_at)).limit(limit)).all()
    return [order_to_dict(order) for order in orders]


def list_reports(db: Session, limit: int = 25) -> list[dict]:
    reports = db.scalars(select(Report).order_by(desc(Report.created_at)).limit(limit)).all()
    return [report_to_dict(report) for report in reports]


def create_report(db: Session, report_create: ReportCreate, current_user: dict) -> dict:
    report = Report(
        name=report_create.name,
        report_type=report_create.report_type,
        status=ReportStatus.QUEUED,
        parameters_json=json.dumps(report_create.parameters or {}),
        created_by_user_id=current_user.get("id"),
    )
    db.add(report)
    db.flush()
    create_audit_log(
        db,
        action=AuditAction.CREATE,
        entity_type="reports",
        entity_id=str(report.id),
        detail=f"Report queued: {report.name}",
    )
    db.commit()
    db.refresh(report)
    return report_to_dict(report)


def list_planning_requests(db: Session, limit: int = 25) -> list[dict]:
    requests = db.scalars(
        select(PlanningRequest).order_by(desc(PlanningRequest.created_at)).limit(limit)
    ).all()
    return [planning_request_to_dict(request) for request in requests]


def create_planning_request(
    db: Session,
    planning_request_create: PlanningRequestCreate,
    current_user: dict,
) -> dict:
    planning_request = PlanningRequest(
        request_number=f"PR-{uuid4().hex[:8].upper()}",
        title=planning_request_create.title,
        description=planning_request_create.description,
        priority=planning_request_create.priority,
        status=PlanningRequestStatus.SUBMITTED,
        requested_by_user_id=current_user.get("id"),
        due_date=planning_request_create.due_date,
    )
    db.add(planning_request)
    db.flush()
    create_audit_log(
        db,
        action=AuditAction.CREATE,
        entity_type="planning_requests",
        entity_id=planning_request.request_number,
        detail=f"Planning request submitted: {planning_request.title}",
    )
    db.commit()
    db.refresh(planning_request)
    return planning_request_to_dict(planning_request)


def list_audit_logs(db: Session, limit: int = 50) -> list[dict]:
    logs = db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)).all()
    return [audit_log_to_dict(log) for log in logs]
