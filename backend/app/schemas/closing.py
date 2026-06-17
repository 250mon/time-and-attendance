import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MonthlyClosingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    year: int
    month: int
    is_locked: bool
    locked_by: uuid.UUID | None
    locked_at: datetime | None
    unlocked_by: uuid.UUID | None
    unlocked_at: datetime | None
    created_at: datetime
    updated_at: datetime
