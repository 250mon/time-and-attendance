from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.services import audit_service as svc

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    action: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditLogResponse]:
    rows = svc.list_audit_logs(db, current_user, action_filter=action, limit=limit, offset=offset)
    return [
        AuditLogResponse(
            id=log.id,
            clinic_id=log.clinic_id,
            actor_id=log.actor_id,
            actor_name=actor_name,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            extra_data=log.extra_data,
            created_at=log.created_at,
        )
        for log, actor_name in rows
    ]
