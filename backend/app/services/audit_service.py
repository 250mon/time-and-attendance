from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction
from app.models.user import User


def log_action(
    db: Session,
    actor_id: UUID,
    clinic_id: UUID,
    action: AuditAction,
    entity_type: str | None = None,
    entity_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Add an audit log entry to the session. Caller is responsible for committing."""
    db.add(AuditLog(
        clinic_id=clinic_id,
        actor_id=actor_id,
        action=action.value,
        entity_type=entity_type,
        entity_id=entity_id,
        extra_data=metadata,
    ))


def list_audit_logs(
    db: Session,
    actor: User,
    action_filter: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[tuple[AuditLog, str]]:
    """Return (AuditLog, actor_name) tuples, newest first."""
    q = (
        db.query(AuditLog, User.name.label("actor_name"))
        .join(User, User.id == AuditLog.actor_id)
        .filter(AuditLog.clinic_id == actor.clinic_id)
    )
    if action_filter:
        q = q.filter(AuditLog.action == action_filter)
    return (
        q.order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
