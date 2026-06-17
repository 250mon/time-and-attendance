from uuid import UUID

from sqlalchemy.orm import Session

from app.core.permissions import can_manage_shifts
from app.models.shift import Shift
from app.models.user import User
from app.schemas.shift import ShiftCreateRequest, ShiftUpdateRequest


class ShiftError(Exception):
    pass


def list_shifts(db: Session, actor: User) -> list[Shift]:
    return (
        db.query(Shift)
        .filter(Shift.clinic_id == actor.clinic_id)
        .order_by(Shift.name.asc())
        .all()
    )


def get_shift(db: Session, actor: User, shift_id: UUID) -> Shift:
    shift = db.get(Shift, shift_id)
    if shift is None or shift.clinic_id != actor.clinic_id:
        raise ShiftError("Shift not found")
    return shift


def create_shift(db: Session, actor: User, payload: ShiftCreateRequest) -> Shift:
    if not can_manage_shifts(actor):
        raise ShiftError("Insufficient permissions")

    shift = Shift(
        clinic_id=actor.clinic_id,
        name=payload.name.strip(),
        start_time=payload.start_time,
        end_time=payload.end_time,
        break_minutes=payload.break_minutes,
        crosses_midnight=payload.crosses_midnight,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


def update_shift(db: Session, actor: User, shift_id: UUID, payload: ShiftUpdateRequest) -> Shift:
    if not can_manage_shifts(actor):
        raise ShiftError("Insufficient permissions")

    shift = get_shift(db, actor, shift_id)
    updates = payload.model_dump(exclude_unset=True)

    if "name" in updates and updates["name"] is not None:
        updates["name"] = updates["name"].strip()

    for field, value in updates.items():
        setattr(shift, field, value)

    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


def deactivate_shift(db: Session, actor: User, shift_id: UUID) -> Shift:
    if not can_manage_shifts(actor):
        raise ShiftError("Insufficient permissions")

    shift = get_shift(db, actor, shift_id)
    shift.active = False
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift
