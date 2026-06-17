from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.permissions import can_manage_schedules
from app.models.leave_request import LeaveRequest
from app.models.enums import AuditAction, LeaveStatus
from app.models.user import User
from app.services.leave_type_service import LeaveTypeError, get_leave_type
from app.services import audit_service, leave_balance_service as balance_svc


class LeaveRequestError(Exception):
    pass


def _total_days(start: date, end: date) -> int:
    return (end - start).days + 1


def create_leave_request(
    db: Session,
    actor: User,
    leave_type_id: UUID,
    start_date: date,
    end_date: date,
    reason: str | None = None,
) -> LeaveRequest:
    if end_date < start_date:
        raise LeaveRequestError("End date must be on or after start date.")

    # Verify leave type belongs to clinic and is active
    try:
        lt = get_leave_type(db, actor.clinic_id, leave_type_id)
    except LeaveTypeError:
        raise LeaveRequestError("Invalid leave type.")
    if not lt.active:
        raise LeaveRequestError("This leave type is no longer active.")

    # No overlapping pending/approved requests
    overlap = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.user_id == actor.id,
            LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )
        .first()
    )
    if overlap:
        raise LeaveRequestError("An overlapping leave request already exists for this period.")

    total = _total_days(start_date, end_date)

    # Check leave balance (uses start_date year for cross-year requests)
    if not balance_svc.has_sufficient_balance(
        db, actor.clinic_id, actor.id, leave_type_id, start_date.year, total
    ):
        raise LeaveRequestError("Not enough leave balance for this request.")

    req = LeaveRequest(
        clinic_id=actor.clinic_id,
        user_id=actor.id,
        leave_type_id=leave_type_id,
        start_date=start_date,
        end_date=end_date,
        total_days=total,
        reason=reason,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def list_leave_requests(
    db: Session,
    actor: User,
    status_filter: LeaveStatus | None = None,
    user_id_filter: UUID | None = None,
) -> list[LeaveRequest]:
    q = db.query(LeaveRequest).filter(LeaveRequest.clinic_id == actor.clinic_id)

    if can_manage_schedules(actor):
        if user_id_filter:
            q = q.filter(LeaveRequest.user_id == user_id_filter)
    else:
        q = q.filter(LeaveRequest.user_id == actor.id)

    if status_filter:
        q = q.filter(LeaveRequest.status == status_filter)

    return q.order_by(LeaveRequest.start_date.desc()).all()


def get_leave_request(db: Session, actor: User, request_id: UUID) -> LeaveRequest:
    req = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not req or req.clinic_id != actor.clinic_id:
        raise LeaveRequestError("Leave request not found.")
    if not can_manage_schedules(actor) and req.user_id != actor.id:
        raise LeaveRequestError("Insufficient permissions.")
    return req


def approve_leave_request(
    db: Session,
    actor: User,
    request_id: UUID,
    reviewer_note: str | None = None,
) -> LeaveRequest:
    from app.services import attendance_calculation_service

    if not can_manage_schedules(actor):
        raise LeaveRequestError("Insufficient permissions.")

    req = get_leave_request(db, actor, request_id)
    if req.user_id == actor.id:
        raise LeaveRequestError("Cannot approve your own leave request.")
    if req.status != LeaveStatus.PENDING:
        raise LeaveRequestError(f"Cannot approve a request with status {req.status}.")

    req.status = LeaveStatus.APPROVED
    req.reviewer_id = actor.id
    req.reviewer_note = reviewer_note
    req.reviewed_at = datetime.now(UTC)

    audit_service.log_action(
        db, actor.id, actor.clinic_id, AuditAction.LEAVE_APPROVED,
        entity_type="leave_request",
        entity_id=str(req.id),
        metadata={
            "user_id": str(req.user_id),
            "start_date": str(req.start_date),
            "end_date": str(req.end_date),
            "total_days": req.total_days,
            "reviewer_note": reviewer_note,
        },
    )
    db.commit()
    db.refresh(req)

    # Deduct balance
    balance_svc.deduct_balance(
        db, req.clinic_id, req.user_id, req.leave_type_id,
        req.start_date.year, req.total_days,
    )
    db.commit()

    # Recalculate attendance for each day in the leave range
    current = req.start_date
    while current <= req.end_date:
        attendance_calculation_service.recalculate_attendance_day(
            db, req.clinic_id, req.user_id, current
        )
        current += timedelta(days=1)

    return req


def reject_leave_request(
    db: Session,
    actor: User,
    request_id: UUID,
    reviewer_note: str | None = None,
) -> LeaveRequest:
    if not can_manage_schedules(actor):
        raise LeaveRequestError("Insufficient permissions.")

    req = get_leave_request(db, actor, request_id)
    if req.user_id == actor.id:
        raise LeaveRequestError("Cannot reject your own leave request.")
    if req.status != LeaveStatus.PENDING:
        raise LeaveRequestError(f"Cannot reject a request with status {req.status}.")

    req.status = LeaveStatus.REJECTED
    req.reviewer_id = actor.id
    req.reviewer_note = reviewer_note
    req.reviewed_at = datetime.now(UTC)

    audit_service.log_action(
        db, actor.id, actor.clinic_id, AuditAction.LEAVE_REJECTED,
        entity_type="leave_request",
        entity_id=str(req.id),
        metadata={
            "user_id": str(req.user_id),
            "start_date": str(req.start_date),
            "end_date": str(req.end_date),
            "reviewer_note": reviewer_note,
        },
    )
    db.commit()
    db.refresh(req)
    return req


def cancel_leave_request(db: Session, actor: User, request_id: UUID) -> LeaveRequest:
    req = get_leave_request(db, actor, request_id)

    if can_manage_schedules(actor) and req.user_id != actor.id:
        # Managers can cancel any pending or approved request for others
        if req.status not in (LeaveStatus.PENDING, LeaveStatus.APPROVED):
            raise LeaveRequestError(f"Cannot cancel a request with status {req.status}.")
    else:
        if req.user_id != actor.id:
            raise LeaveRequestError("You can only cancel your own leave requests.")
        if req.status != LeaveStatus.PENDING:
            raise LeaveRequestError(f"Cannot cancel a request with status {req.status}.")

    was_approved = req.status == LeaveStatus.APPROVED
    req.status = LeaveStatus.CANCELLED
    db.commit()
    db.refresh(req)

    # Restore balance if cancelling an already-approved request
    if was_approved:
        balance_svc.restore_balance(
            db, req.clinic_id, req.user_id, req.leave_type_id,
            req.start_date.year, req.total_days,
        )
        db.commit()

    return req
