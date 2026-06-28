from datetime import UTC, date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.clinic_time import clinic_tz
from app.core.permissions import can_manage_schedules
from app.models.attendance_correction import AttendanceCorrectionRequest
from app.models.clinic import Clinic
from app.models.enums import AuditAction, CorrectionStatus
from app.models.user import User
from app.services import audit_service
from app.services.closing_service import is_month_locked


class CorrectionError(Exception):
    pass


def _parse_time(hhmm: str) -> time:
    """Parse 'HH:MM' string into a time object."""
    parts = hhmm.strip().split(":")
    if len(parts) != 2:
        raise CorrectionError(f"Invalid time format: {hhmm!r}. Use HH:MM.")
    try:
        return time(int(parts[0]), int(parts[1]))
    except ValueError:
        raise CorrectionError(f"Invalid time value: {hhmm!r}.")


def _to_utc(work_date: date, hhmm: str, tz: ZoneInfo) -> datetime:
    """Convert HH:MM on work_date (clinic local time) to a UTC datetime."""
    t = _parse_time(hhmm)
    local_dt = datetime(work_date.year, work_date.month, work_date.day, t.hour, t.minute, tzinfo=tz)
    return local_dt.astimezone(UTC)


def create_correction(
    db: Session,
    actor: User,
    work_date: date,
    reason: str,
    corrected_clock_in: str | None = None,
    corrected_clock_out: str | None = None,
) -> AttendanceCorrectionRequest:
    today = datetime.now(UTC).date()

    if work_date >= today:
        raise CorrectionError("Corrections can only be submitted for past dates.")

    if is_month_locked(db, actor.clinic_id, work_date.year, work_date.month):
        raise CorrectionError(
            f"{work_date.year}-{work_date.month:02d} is locked and cannot be modified."
        )

    if not reason or not reason.strip():
        raise CorrectionError("Reason is required.")

    if corrected_clock_in is None and corrected_clock_out is None:
        raise CorrectionError("At least one corrected time must be provided.")

    clinic = db.get(Clinic, actor.clinic_id)
    tz = clinic_tz(clinic.timezone if clinic else None)
    ci_utc = _to_utc(work_date, corrected_clock_in, tz) if corrected_clock_in else None
    co_utc = _to_utc(work_date, corrected_clock_out, tz) if corrected_clock_out else None

    if ci_utc and co_utc and co_utc <= ci_utc:
        raise CorrectionError("Corrected clock-out must be after corrected clock-in.")

    existing_pending = (
        db.query(AttendanceCorrectionRequest)
        .filter(
            AttendanceCorrectionRequest.user_id == actor.id,
            AttendanceCorrectionRequest.work_date == work_date,
            AttendanceCorrectionRequest.status == CorrectionStatus.PENDING,
        )
        .first()
    )
    if existing_pending:
        raise CorrectionError("A pending correction already exists for this date. Cancel it first.")

    req = AttendanceCorrectionRequest(
        clinic_id=actor.clinic_id,
        user_id=actor.id,
        work_date=work_date,
        reason=reason.strip(),
        corrected_clock_in=ci_utc,
        corrected_clock_out=co_utc,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def list_corrections(
    db: Session,
    actor: User,
    status_filter: CorrectionStatus | None = None,
    user_id_filter: UUID | None = None,
) -> list[AttendanceCorrectionRequest]:
    q = db.query(AttendanceCorrectionRequest).filter(
        AttendanceCorrectionRequest.clinic_id == actor.clinic_id
    )

    if can_manage_schedules(actor):
        if user_id_filter:
            q = q.filter(AttendanceCorrectionRequest.user_id == user_id_filter)
    else:
        q = q.filter(AttendanceCorrectionRequest.user_id == actor.id)

    if status_filter:
        q = q.filter(AttendanceCorrectionRequest.status == status_filter)

    return q.order_by(AttendanceCorrectionRequest.created_at.desc()).all()


def get_correction(db: Session, actor: User, correction_id: UUID) -> AttendanceCorrectionRequest:
    req = (
        db.query(AttendanceCorrectionRequest)
        .filter(AttendanceCorrectionRequest.id == correction_id)
        .first()
    )
    if not req:
        raise CorrectionError("Correction request not found.")
    if req.clinic_id != actor.clinic_id:
        raise CorrectionError("Not found.")
    if not can_manage_schedules(actor) and req.user_id != actor.id:
        raise CorrectionError("Insufficient permissions.")
    return req


def approve_correction(
    db: Session,
    actor: User,
    correction_id: UUID,
    reviewer_note: str | None = None,
) -> AttendanceCorrectionRequest:
    from app.services import attendance_calculation_service

    req = get_correction(db, actor, correction_id)

    if not can_manage_schedules(actor):
        raise CorrectionError("Insufficient permissions.")
    if req.user_id == actor.id:
        raise CorrectionError("Cannot approve your own correction request.")
    if req.status != CorrectionStatus.PENDING:
        raise CorrectionError(f"Cannot approve a request with status {req.status}.")
    if is_month_locked(db, req.clinic_id, req.work_date.year, req.work_date.month):
        raise CorrectionError(
            f"{req.work_date.year}-{req.work_date.month:02d} is locked. Unlock it before approving corrections."
        )

    req.status = CorrectionStatus.APPROVED
    req.reviewer_id = actor.id
    req.reviewer_note = reviewer_note
    req.reviewed_at = datetime.now(UTC)

    audit_service.log_action(
        db, actor.id, actor.clinic_id, AuditAction.CORRECTION_APPROVED,
        entity_type="correction",
        entity_id=str(req.id),
        metadata={
            "work_date": str(req.work_date),
            "user_id": str(req.user_id),
            "reviewer_note": reviewer_note,
        },
    )
    db.commit()
    db.refresh(req)

    attendance_calculation_service.recalculate_attendance_day(
        db, req.clinic_id, req.user_id, req.work_date
    )
    return req


def reject_correction(
    db: Session,
    actor: User,
    correction_id: UUID,
    reviewer_note: str | None = None,
) -> AttendanceCorrectionRequest:
    req = get_correction(db, actor, correction_id)

    if not can_manage_schedules(actor):
        raise CorrectionError("Insufficient permissions.")
    if req.user_id == actor.id:
        raise CorrectionError("Cannot reject your own correction request.")
    if req.status != CorrectionStatus.PENDING:
        raise CorrectionError(f"Cannot reject a request with status {req.status}.")

    req.status = CorrectionStatus.REJECTED
    req.reviewer_id = actor.id
    req.reviewer_note = reviewer_note
    req.reviewed_at = datetime.now(UTC)

    audit_service.log_action(
        db, actor.id, actor.clinic_id, AuditAction.CORRECTION_REJECTED,
        entity_type="correction",
        entity_id=str(req.id),
        metadata={
            "work_date": str(req.work_date),
            "user_id": str(req.user_id),
            "reviewer_note": reviewer_note,
        },
    )
    db.commit()
    db.refresh(req)
    return req


def cancel_correction(
    db: Session,
    actor: User,
    correction_id: UUID,
) -> AttendanceCorrectionRequest:
    req = get_correction(db, actor, correction_id)

    if req.user_id != actor.id:
        raise CorrectionError("You can only cancel your own correction requests.")
    if req.status != CorrectionStatus.PENDING:
        raise CorrectionError(f"Cannot cancel a request with status {req.status}.")

    req.status = CorrectionStatus.CANCELLED
    db.commit()
    db.refresh(req)
    return req
