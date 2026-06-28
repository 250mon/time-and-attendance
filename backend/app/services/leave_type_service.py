from uuid import UUID

from sqlalchemy.orm import Session

from app.core.permissions import can_manage_schedules
from app.models.leave_type import LeaveType
from app.models.user import User


class LeaveTypeError(Exception):
    pass


def list_leave_types(db: Session, clinic_id: UUID, include_inactive: bool = False) -> list[LeaveType]:
    q = db.query(LeaveType).filter(LeaveType.clinic_id == clinic_id)
    if not include_inactive:
        q = q.filter(LeaveType.active.is_(True))
    return q.order_by(LeaveType.name).all()


def get_leave_type(db: Session, clinic_id: UUID, leave_type_id: UUID) -> LeaveType:
    lt = db.query(LeaveType).filter(
        LeaveType.id == leave_type_id,
        LeaveType.clinic_id == clinic_id,
    ).first()
    if not lt:
        raise LeaveTypeError("Leave type not found.")
    return lt


def get_leave_type_or_none(db: Session, clinic_id: UUID, leave_type_id: UUID) -> LeaveType | None:
    return db.query(LeaveType).filter(
        LeaveType.id == leave_type_id,
        LeaveType.clinic_id == clinic_id,
    ).first()


_NULLABLE_FIELDS = {"default_days_per_year", "carryover_max_days"}


def create_leave_type(
    db: Session,
    actor: User,
    name: str,
    default_days_per_year: int | None = None,
    requires_approval: bool = True,
    tenure_based: bool = False,
    allow_carryover: bool = False,
    carryover_max_days: int | None = None,
) -> LeaveType:
    if not can_manage_schedules(actor):
        raise LeaveTypeError("Insufficient permissions.")
    if not name or not name.strip():
        raise LeaveTypeError("Name is required.")

    lt = LeaveType(
        clinic_id=actor.clinic_id,
        name=name.strip(),
        default_days_per_year=default_days_per_year,
        requires_approval=requires_approval,
        tenure_based=tenure_based,
        allow_carryover=allow_carryover,
        carryover_max_days=carryover_max_days,
    )
    db.add(lt)
    db.commit()
    db.refresh(lt)
    return lt


def update_leave_type(
    db: Session,
    actor: User,
    leave_type_id: UUID,
    **kwargs,
) -> LeaveType:
    if not can_manage_schedules(actor):
        raise LeaveTypeError("Insufficient permissions.")
    lt = get_leave_type(db, actor.clinic_id, leave_type_id)
    for field, value in kwargs.items():
        if value is not None or field in _NULLABLE_FIELDS:
            setattr(lt, field, value)
    db.commit()
    db.refresh(lt)
    return lt


def deactivate_leave_type(db: Session, actor: User, leave_type_id: UUID) -> LeaveType:
    if not can_manage_schedules(actor):
        raise LeaveTypeError("Insufficient permissions.")
    lt = get_leave_type(db, actor.clinic_id, leave_type_id)
    lt.active = False
    db.commit()
    db.refresh(lt)
    return lt
