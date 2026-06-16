from sqlalchemy.orm import Session

from ..models import AuditAction, AuditLog, User


def create_audit_log(
    db: Session,
    *,
    action: AuditAction,
    entity_type: str,
    entity_id: str | None = None,
    actor: User | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Persist an audit event without committing the outer transaction."""
    log = AuditLog(
        actor_user_id=actor.id if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    return log
