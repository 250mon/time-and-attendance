import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: uuid.UUID
    clinic_id: uuid.UUID
    actor_id: uuid.UUID
    actor_name: str
    action: str
    entity_type: str | None
    entity_id: str | None
    extra_data: dict[str, Any] | None
    created_at: datetime
