from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.permissions import can_manage_schedules
from app.models.attendance_punch import AttendancePunch
from app.models.enums import PunchSource, PunchType
from app.models.staff_schedule import StaffSchedule
from app.models.user import User
from app.services import attendance_calculation_service


class AttendanceError(Exception):
    pass


def _day_bounds(d: date) -> tuple[datetime, datetime]:
    """Return UTC midnight start and exclusive end for a calendar date."""
    start = datetime(d.year, d.month, d.day, tzinfo=UTC)
    return start, start + timedelta(days=1)


def _last_relevant_punch(db: Session, user_id: UUID, for_date: date) -> AttendancePunch | None:
    start, end = _day_bounds(for_date)
    return (
        db.query(AttendancePunch)
        .filter(
            AttendancePunch.user_id == user_id,
            AttendancePunch.punch_type.in_([PunchType.CLOCK_IN, PunchType.CLOCK_OUT]),
            AttendancePunch.punched_at >= start,
            AttendancePunch.punched_at < end,
        )
        .order_by(AttendancePunch.punched_at.desc())
        .first()
    )


def _is_clocked_in(db: Session, user_id: UUID, for_date: date) -> bool:
    punch = _last_relevant_punch(db, user_id, for_date)
    return punch is not None and punch.punch_type == PunchType.CLOCK_IN


def _today() -> date:
    return datetime.now(UTC).date()


def clock_in(db: Session, actor: User, ip_address: str | None = None) -> AttendancePunch:
    today = _today()
    if _is_clocked_in(db, actor.id, today):
        raise AttendanceError("Already clocked in")

    punch = AttendancePunch(
        clinic_id=actor.clinic_id,
        user_id=actor.id,
        punch_type=PunchType.CLOCK_IN,
        punched_at=datetime.now(UTC),
        source=PunchSource.WEB,
        ip_address=ip_address,
    )
    db.add(punch)
    db.commit()
    db.refresh(punch)
    attendance_calculation_service.recalculate_attendance_day(
        db, actor.clinic_id, actor.id, today
    )
    return punch


def clock_out(db: Session, actor: User, ip_address: str | None = None) -> AttendancePunch:
    today = _today()
    if not _is_clocked_in(db, actor.id, today):
        raise AttendanceError("No active clock-in found")

    punch = AttendancePunch(
        clinic_id=actor.clinic_id,
        user_id=actor.id,
        punch_type=PunchType.CLOCK_OUT,
        punched_at=datetime.now(UTC),
        source=PunchSource.WEB,
        ip_address=ip_address,
    )
    db.add(punch)
    db.commit()
    db.refresh(punch)
    attendance_calculation_service.recalculate_attendance_day(
        db, actor.clinic_id, actor.id, today
    )
    return punch


def get_today_status(db: Session, actor: User) -> dict:
    today = _today()
    start, end = _day_bounds(today)

    punches = (
        db.query(AttendancePunch)
        .filter(
            AttendancePunch.user_id == actor.id,
            AttendancePunch.punched_at >= start,
            AttendancePunch.punched_at < end,
        )
        .order_by(AttendancePunch.punched_at.asc())
        .all()
    )

    schedule = (
        db.query(StaffSchedule)
        .filter(
            StaffSchedule.user_id == actor.id,
            StaffSchedule.work_date == today,
        )
        .first()
    )

    return {
        "work_date": today,
        "is_clocked_in": _is_clocked_in(db, actor.id, today),
        "punches": punches,
        "schedule": schedule,
        "last_punch": punches[-1] if punches else None,
    }


def get_my_punches(db: Session, actor: User, days: int = 30) -> list[AttendancePunch]:
    since = datetime.now(UTC) - timedelta(days=days)
    return (
        db.query(AttendancePunch)
        .filter(
            AttendancePunch.user_id == actor.id,
            AttendancePunch.punched_at >= since,
        )
        .order_by(AttendancePunch.punched_at.desc())
        .all()
    )


def get_daily_punches(db: Session, actor: User, for_date: date) -> list[dict]:
    """Return all users' punches for a given date grouped by user. Manager+ only."""
    if not can_manage_schedules(actor):
        raise AttendanceError("Insufficient permissions")

    start, end = _day_bounds(for_date)
    punches = (
        db.query(AttendancePunch)
        .filter(
            AttendancePunch.clinic_id == actor.clinic_id,
            AttendancePunch.punched_at >= start,
            AttendancePunch.punched_at < end,
        )
        .order_by(AttendancePunch.user_id, AttendancePunch.punched_at.asc())
        .all()
    )

    # Group by user
    by_user: dict[UUID, list[AttendancePunch]] = {}
    for p in punches:
        by_user.setdefault(p.user_id, []).append(p)

    users = {
        u.id: u.name
        for u in db.query(User).filter(
            User.clinic_id == actor.clinic_id,
            User.id.in_(by_user.keys()),
        )
    }

    return [
        {
            "user_id": uid,
            "user_name": users.get(uid, str(uid)),
            "punches": user_punches,
            "is_clocked_in": _is_clocked_in(db, uid, for_date),
        }
        for uid, user_punches in by_user.items()
    ]


def get_monthly_punches(
    db: Session, actor: User, year: int, month: int
) -> list[AttendancePunch]:
    """Return all clinic punches for a month. Manager+ only."""
    if not can_manage_schedules(actor):
        raise AttendanceError("Insufficient permissions")

    start = datetime(year, month, 1, tzinfo=UTC)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(year, month + 1, 1, tzinfo=UTC)

    return (
        db.query(AttendancePunch)
        .filter(
            AttendancePunch.clinic_id == actor.clinic_id,
            AttendancePunch.punched_at >= start,
            AttendancePunch.punched_at < end,
        )
        .order_by(AttendancePunch.user_id, AttendancePunch.punched_at.asc())
        .all()
    )
