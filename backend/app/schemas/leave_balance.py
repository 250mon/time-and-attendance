import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LeaveBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    user_id: uuid.UUID
    leave_type_id: uuid.UUID
    year: int
    balance_days: float
    used_days: float
    remaining_days: float
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_with_remaining(cls, obj: object) -> "LeaveBalanceResponse":
        data = {
            "id": obj.id,  # type: ignore[attr-defined]
            "clinic_id": obj.clinic_id,  # type: ignore[attr-defined]
            "user_id": obj.user_id,  # type: ignore[attr-defined]
            "leave_type_id": obj.leave_type_id,  # type: ignore[attr-defined]
            "year": obj.year,  # type: ignore[attr-defined]
            "balance_days": float(obj.balance_days),  # type: ignore[attr-defined]
            "used_days": float(obj.used_days),  # type: ignore[attr-defined]
            "remaining_days": float(obj.balance_days - obj.used_days),  # type: ignore[attr-defined]
            "created_at": obj.created_at,  # type: ignore[attr-defined]
            "updated_at": obj.updated_at,  # type: ignore[attr-defined]
        }
        return cls(**data)


class AdjustBalanceRequest(BaseModel):
    user_id: uuid.UUID
    leave_type_id: uuid.UUID
    year: int = Field(..., ge=2000, le=2100)
    delta_days: float = Field(..., ge=-365, le=365)
    reason: str = Field(..., min_length=1, max_length=500)
