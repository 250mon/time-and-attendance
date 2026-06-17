"""
Deterministic attendance calculation engine.

Given a user + work_date, reads punches and schedule, computes all derived
minute fields and status, then upserts a single attendance_days row.

Same inputs always produce the same output (no side effects beyond the upsert).
"""

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.attendance_correction import AttendanceCorrectionRequest
from app.models.attendance_day import AttendanceDay
from app.models.attendance_punch import AttendancePunch
from app.models.enums import AttendanceDayStatus, CorrectionStatus, LeaveStatus, PunchType, ScheduleStatus
from app.models.leave_request import LeaveRequest
from app.models.staff_schedule import StaffSchedule


def _tz() -> ZoneInfo:
    return ZoneInfo(settings.clinic_timezone)


def _utc_day_bounds(d: date) -> tuple[datetime, datetime]:
    start = datetime(d.year, d.month, d.day, tzinfo=UTC)
    return start, start + timedelta(days=1)


def _scheduled_utc(work_date: date, t: time) -> datetime:
    """Combine a work_date + local time-of-day into a UTC datetime."""
    local = datetime(work_date.year, work_date.month, work_date.day, t.hour, t.minute, t.second, tzinfo=_tz())
    return local.astimezone(UTC)


def recalculate_attendance_day(
    db: Session,
    clinic_id: UUID,
    user_id: UUID,
    work_date: date,
) -> AttendanceDay:
    schedule = (
        db.query(StaffSchedule)
        .filter(StaffSchedule.user_id == user_id, StaffSchedule.work_date == work_date)
        .first()
    )

    start_utc, end_utc = _utc_day_bounds(work_date)
    punches: list[AttendancePunch] = (
        db.query(AttendancePunch)
        .filter(
            AttendancePunch.user_id == user_id,
            AttendancePunch.punched_at >= start_utc,
            AttendancePunch.punched_at < end_utc,
        )
        .order_by(AttendancePunch.punched_at.asc())
        .all()
    )

    clock_ins = [p for p in punches if p.punch_type == PunchType.CLOCK_IN]
    clock_outs = [p for p in punches if p.punch_type == PunchType.CLOCK_OUT]
    actual_clock_in = clock_ins[0].punched_at if clock_ins else None
    actual_clock_out = clock_outs[-1].punched_at if clock_outs else None

    # Apply approved correction if one exists (most recent wins)
    correction = (
        db.query(AttendanceCorrectionRequest)
        .filter(
            AttendanceCorrectionRequest.user_id == user_id,
            AttendanceCorrectionRequest.work_date == work_date,
            AttendanceCorrectionRequest.status == CorrectionStatus.APPROVED,
        )
        .order_by(AttendanceCorrectionRequest.reviewed_at.desc())
        .first()
    )
    if correction:
        if correction.corrected_clock_in is not None:
            actual_clock_in = correction.corrected_clock_in
        if correction.corrected_clock_out is not None:
            actual_clock_out = correction.corrected_clock_out

    # Scheduled window in UTC
    sched_start_utc: datetime | None = None
    sched_end_utc: datetime | None = None
    scheduled_minutes: int | None = None

    if schedule and schedule.scheduled_start and schedule.scheduled_end:
        sched_start_utc = _scheduled_utc(work_date, schedule.scheduled_start)
        sched_end_utc = _scheduled_utc(work_date, schedule.scheduled_end)
        if schedule.scheduled_end < schedule.scheduled_start:
            # shift crosses midnight in local time
            sched_end_utc += timedelta(days=1)
        gross = int((sched_end_utc - sched_start_utc).total_seconds() / 60)
        scheduled_minutes = max(0, gross - schedule.scheduled_break_minutes)

    # Break minutes from actual BREAK_START/BREAK_END pairs
    break_minutes = 0
    break_starts = [p for p in punches if p.punch_type == PunchType.BREAK_START]
    break_ends = [p for p in punches if p.punch_type == PunchType.BREAK_END]
    for bs, be in zip(break_starts, break_ends):
        if be.punched_at > bs.punched_at:
            break_minutes += int((be.punched_at - bs.punched_at).total_seconds() / 60)

    # Worked minutes
    worked_minutes = 0
    if actual_clock_in and actual_clock_out:
        raw = int((actual_clock_out - actual_clock_in).total_seconds() / 60)
        # Use recorded break pairs if any; fall back to scheduled break allowance
        effective_break = break_minutes if break_minutes > 0 else (
            schedule.scheduled_break_minutes if schedule else 0
        )
        worked_minutes = max(0, raw - effective_break)
        if break_minutes == 0 and schedule:
            break_minutes = schedule.scheduled_break_minutes

    # Regular / overtime split
    regular_minutes = 0
    overtime_minutes = 0
    if worked_minutes > 0:
        if scheduled_minutes is not None:
            regular_minutes = min(worked_minutes, scheduled_minutes)
            overtime_minutes = max(0, worked_minutes - scheduled_minutes)
        else:
            regular_minutes = worked_minutes

    # Late / early-leave
    late_minutes = 0
    early_leave_minutes = 0
    if sched_start_utc and actual_clock_in:
        late_minutes = max(0, int((actual_clock_in - sched_start_utc).total_seconds() / 60))
    if sched_end_utc and actual_clock_out:
        early_leave_minutes = max(0, int((sched_end_utc - actual_clock_out).total_seconds() / 60))

    # Status
    today = datetime.now(UTC).date()
    if schedule and schedule.status == ScheduleStatus.HOLIDAY:
        status = AttendanceDayStatus.HOLIDAY
    elif actual_clock_in is None:
        if work_date < today:
            status = AttendanceDayStatus.ABSENT
        else:
            status = AttendanceDayStatus.NOT_STARTED
    elif actual_clock_out is None:
        status = AttendanceDayStatus.WORKING
    else:
        status = AttendanceDayStatus.COMPLETED

    # Approved leave overrides absent/not-started status (but not holiday/working/completed)
    if status in (AttendanceDayStatus.ABSENT, AttendanceDayStatus.NOT_STARTED):
        leave = (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.user_id == user_id,
                LeaveRequest.start_date <= work_date,
                LeaveRequest.end_date >= work_date,
                LeaveRequest.status == LeaveStatus.APPROVED,
            )
            .first()
        )
        if leave:
            status = AttendanceDayStatus.ON_LEAVE

    # Upsert
    existing = (
        db.query(AttendanceDay)
        .filter(AttendanceDay.user_id == user_id, AttendanceDay.work_date == work_date)
        .first()
    )

    if existing:
        if existing.is_locked:
            return existing
        existing.status = status
        existing.scheduled_minutes = scheduled_minutes
        existing.actual_clock_in = actual_clock_in
        existing.actual_clock_out = actual_clock_out
        existing.worked_minutes = worked_minutes
        existing.regular_minutes = regular_minutes
        existing.overtime_minutes = overtime_minutes
        existing.late_minutes = late_minutes
        existing.early_leave_minutes = early_leave_minutes
        existing.break_minutes = break_minutes
        db.commit()
        db.refresh(existing)
        return existing

    day = AttendanceDay(
        clinic_id=clinic_id,
        user_id=user_id,
        work_date=work_date,
        status=status,
        scheduled_minutes=scheduled_minutes,
        actual_clock_in=actual_clock_in,
        actual_clock_out=actual_clock_out,
        worked_minutes=worked_minutes,
        regular_minutes=regular_minutes,
        overtime_minutes=overtime_minutes,
        late_minutes=late_minutes,
        early_leave_minutes=early_leave_minutes,
        break_minutes=break_minutes,
    )
    db.add(day)
    db.commit()
    db.refresh(day)
    return day


def get_attendance_days(
    db: Session,
    clinic_id: UUID,
    user_id: UUID,
    start_date: date,
    end_date: date,
    filter_user_id: UUID | None = None,
) -> list[AttendanceDay]:
    """
    Returns attendance_days rows for the given date range.

    If filter_user_id is provided, restricts to that user (manager use-case).
    Otherwise returns rows for user_id only (self view).
    """
    q = db.query(AttendanceDay).filter(
        AttendanceDay.clinic_id == clinic_id,
        AttendanceDay.work_date >= start_date,
        AttendanceDay.work_date <= end_date,
    )
    if filter_user_id is not None:
        q = q.filter(AttendanceDay.user_id == filter_user_id)
    else:
        q = q.filter(AttendanceDay.user_id == user_id)
    return q.order_by(AttendanceDay.work_date.desc()).all()
