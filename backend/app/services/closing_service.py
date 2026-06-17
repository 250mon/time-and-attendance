from calendar import monthrange
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.attendance_day import AttendanceDay
from app.models.enums import AuditAction, UserRole
from app.models.monthly_closing import MonthlyClosing
from app.models.user import User
from app.services import audit_service


class ClosingError(Exception):
    pass


def _can_manage(actor: User) -> bool:
    return actor.role in (UserRole.OWNER, UserRole.ADMIN)


def _month_date_range(year: int, month: int) -> tuple[date, date]:
    _, last_day = monthrange(year, month)
    return date(year, month, 1), date(year, month, last_day)


def get_or_create_closing(db: Session, clinic_id: UUID, year: int, month: int) -> MonthlyClosing:
    closing = (
        db.query(MonthlyClosing)
        .filter(
            MonthlyClosing.clinic_id == clinic_id,
            MonthlyClosing.year == year,
            MonthlyClosing.month == month,
        )
        .first()
    )
    if not closing:
        closing = MonthlyClosing(clinic_id=clinic_id, year=year, month=month, is_locked=False)
        db.add(closing)
        db.flush()
    return closing


def is_month_locked(db: Session, clinic_id: UUID, year: int, month: int) -> bool:
    closing = (
        db.query(MonthlyClosing)
        .filter(
            MonthlyClosing.clinic_id == clinic_id,
            MonthlyClosing.year == year,
            MonthlyClosing.month == month,
        )
        .first()
    )
    return closing is not None and closing.is_locked


def lock_month(db: Session, actor: User, year: int, month: int) -> MonthlyClosing:
    if not _can_manage(actor):
        raise ClosingError("Only owners and admins can lock months.")

    closing = get_or_create_closing(db, actor.clinic_id, year, month)
    if closing.is_locked:
        raise ClosingError(f"{year}-{month:02d} is already locked.")

    closing.is_locked = True
    closing.locked_by = actor.id
    closing.locked_at = datetime.now(UTC)

    start, end = _month_date_range(year, month)
    db.query(AttendanceDay).filter(
        AttendanceDay.clinic_id == actor.clinic_id,
        AttendanceDay.work_date >= start,
        AttendanceDay.work_date <= end,
    ).update({"is_locked": True}, synchronize_session=False)

    audit_service.log_action(
        db, actor.id, actor.clinic_id, AuditAction.MONTH_LOCKED,
        entity_type="monthly_closing",
        entity_id=str(closing.id),
        metadata={"year": year, "month": month},
    )
    db.commit()
    db.refresh(closing)
    return closing


def unlock_month(db: Session, actor: User, year: int, month: int) -> MonthlyClosing:
    if not _can_manage(actor):
        raise ClosingError("Only owners and admins can unlock months.")

    closing = (
        db.query(MonthlyClosing)
        .filter(
            MonthlyClosing.clinic_id == actor.clinic_id,
            MonthlyClosing.year == year,
            MonthlyClosing.month == month,
        )
        .first()
    )
    if not closing or not closing.is_locked:
        raise ClosingError(f"{year}-{month:02d} is not locked.")

    closing.is_locked = False
    closing.unlocked_by = actor.id
    closing.unlocked_at = datetime.now(UTC)

    start, end = _month_date_range(year, month)
    db.query(AttendanceDay).filter(
        AttendanceDay.clinic_id == actor.clinic_id,
        AttendanceDay.work_date >= start,
        AttendanceDay.work_date <= end,
    ).update({"is_locked": False}, synchronize_session=False)

    audit_service.log_action(
        db, actor.id, actor.clinic_id, AuditAction.MONTH_UNLOCKED,
        entity_type="monthly_closing",
        entity_id=str(closing.id),
        metadata={"year": year, "month": month},
    )
    db.commit()
    db.refresh(closing)
    return closing


def list_closings(db: Session, clinic_id: UUID, year: int | None = None) -> list[MonthlyClosing]:
    q = db.query(MonthlyClosing).filter(MonthlyClosing.clinic_id == clinic_id)
    if year:
        q = q.filter(MonthlyClosing.year == year)
    return q.order_by(MonthlyClosing.year.desc(), MonthlyClosing.month.desc()).all()
