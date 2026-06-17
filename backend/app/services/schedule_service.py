from datetime import timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.permissions import can_manage_schedules
from app.models.enums import ScheduleStatus
from app.models.shift import Shift
from app.models.staff_schedule import StaffSchedule
from app.models.user import User
from app.schemas.schedule import (
    ScheduleCreateRequest,
    ScheduleGenerateRequest,
    ScheduleUpdateRequest,
)


class ScheduleError(Exception):
    pass


def _get_shift_for_clinic(db: Session, shift_id: UUID, clinic_id: UUID) -> Shift:
    shift = db.get(Shift, shift_id)
    if shift is None or shift.clinic_id != clinic_id:
        raise ScheduleError("Shift not found")
    return shift


def _get_user_for_clinic(db: Session, user_id: UUID, clinic_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None or user.clinic_id != clinic_id:
        raise ScheduleError("User not found")
    return user


def list_schedules(
    db: Session,
    actor: User,
    start_date: object = None,
    end_date: object = None,
    user_id: UUID | None = None,
) -> list[StaffSchedule]:
    query = db.query(StaffSchedule).filter(StaffSchedule.clinic_id == actor.clinic_id)

    if not can_manage_schedules(actor):
        query = query.filter(StaffSchedule.user_id == actor.id)
    elif user_id is not None:
        query = query.filter(StaffSchedule.user_id == user_id)

    if start_date is not None:
        query = query.filter(StaffSchedule.work_date >= start_date)
    if end_date is not None:
        query = query.filter(StaffSchedule.work_date <= end_date)

    return query.order_by(StaffSchedule.work_date.asc(), StaffSchedule.user_id.asc()).all()


def get_schedule(db: Session, actor: User, schedule_id: UUID) -> StaffSchedule:
    schedule = db.get(StaffSchedule, schedule_id)
    if schedule is None or schedule.clinic_id != actor.clinic_id:
        raise ScheduleError("Schedule not found")
    if not can_manage_schedules(actor) and schedule.user_id != actor.id:
        raise ScheduleError("Insufficient permissions")
    return schedule


def create_schedule(db: Session, actor: User, payload: ScheduleCreateRequest) -> StaffSchedule:
    if not can_manage_schedules(actor):
        raise ScheduleError("Insufficient permissions")

    _get_user_for_clinic(db, payload.user_id, actor.clinic_id)

    scheduled_start = payload.scheduled_start
    scheduled_end = payload.scheduled_end
    scheduled_break_minutes = payload.scheduled_break_minutes

    if payload.shift_id is not None:
        shift = _get_shift_for_clinic(db, payload.shift_id, actor.clinic_id)
        if scheduled_start is None:
            scheduled_start = shift.start_time
            scheduled_end = shift.end_time
            scheduled_break_minutes = shift.break_minutes

    existing = (
        db.query(StaffSchedule)
        .filter(
            StaffSchedule.user_id == payload.user_id,
            StaffSchedule.work_date == payload.work_date,
        )
        .one_or_none()
    )
    if existing is not None:
        raise ScheduleError("A schedule already exists for this user on this date")

    schedule = StaffSchedule(
        clinic_id=actor.clinic_id,
        user_id=payload.user_id,
        shift_id=payload.shift_id,
        work_date=payload.work_date,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        scheduled_break_minutes=scheduled_break_minutes,
        status=payload.status,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def update_schedule(
    db: Session, actor: User, schedule_id: UUID, payload: ScheduleUpdateRequest
) -> StaffSchedule:
    if not can_manage_schedules(actor):
        raise ScheduleError("Insufficient permissions")

    schedule = get_schedule(db, actor, schedule_id)
    updates = payload.model_dump(exclude_unset=True)

    if "shift_id" in updates and updates["shift_id"] is not None:
        _get_shift_for_clinic(db, updates["shift_id"], actor.clinic_id)

    for field, value in updates.items():
        setattr(schedule, field, value)

    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, actor: User, schedule_id: UUID) -> None:
    if not can_manage_schedules(actor):
        raise ScheduleError("Insufficient permissions")

    schedule = get_schedule(db, actor, schedule_id)
    db.delete(schedule)
    db.commit()


def generate_schedules(
    db: Session, actor: User, payload: ScheduleGenerateRequest
) -> list[StaffSchedule]:
    if not can_manage_schedules(actor):
        raise ScheduleError("Insufficient permissions")

    _get_user_for_clinic(db, payload.user_id, actor.clinic_id)
    shift = _get_shift_for_clinic(db, payload.shift_id, actor.clinic_id)

    created: list[StaffSchedule] = []
    current = payload.start_date
    while current <= payload.end_date:
        if current.weekday() in payload.weekdays:
            exists = (
                db.query(StaffSchedule)
                .filter(
                    StaffSchedule.user_id == payload.user_id,
                    StaffSchedule.work_date == current,
                )
                .one_or_none()
            )
            if exists is None:
                schedule = StaffSchedule(
                    clinic_id=actor.clinic_id,
                    user_id=payload.user_id,
                    shift_id=payload.shift_id,
                    work_date=current,
                    scheduled_start=shift.start_time,
                    scheduled_end=shift.end_time,
                    scheduled_break_minutes=shift.break_minutes,
                    status=ScheduleStatus.SCHEDULED,
                )
                db.add(schedule)
                created.append(schedule)
        current += timedelta(days=1)

    db.commit()
    for s in created:
        db.refresh(s)
    return created
