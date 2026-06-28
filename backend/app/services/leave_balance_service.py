from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.clinic_time import clinic_today
from app.core.kr_labor import annual_leave_for_calendar_year, as_of_date_for_balance_year
from app.core.permissions import can_manage_schedules
from app.models.clinic import Clinic
from app.models.enums import AuditAction
from app.models.leave_balance import LeaveBalance, LeaveBalanceAdjustment
from app.models.leave_type import LeaveType
from app.models.user import User
from app.services import audit_service


class LeaveBalanceError(Exception):
    pass


def _dec(value: float | int | Decimal) -> Decimal:
    return Decimal(str(value))


def _get_leave_type(db: Session, leave_type_id: UUID) -> LeaveType | None:
    return db.query(LeaveType).filter(LeaveType.id == leave_type_id).first()


def _clinic_today(db: Session, clinic_id: UUID) -> date:
    clinic = db.get(Clinic, clinic_id)
    return clinic_today(clinic.timezone if clinic else None)


def get_or_create_balance(
    db: Session,
    clinic_id: UUID,
    user_id: UUID,
    leave_type_id: UUID,
    year: int,
    *,
    for_usage_only: bool = False,
) -> LeaveBalance:
    lt = _get_leave_type(db, leave_type_id)

    balance = (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.user_id == user_id,
            LeaveBalance.leave_type_id == leave_type_id,
            LeaveBalance.year == year,
        )
        .first()
    )

    if lt and not lt.tenure_based:
        if balance is not None:
            return balance
        if not for_usage_only:
            raise LeaveBalanceError("This leave type does not use yearly allocation.")
        balance = LeaveBalance(
            clinic_id=clinic_id,
            user_id=user_id,
            leave_type_id=leave_type_id,
            year=year,
            balance_days=Decimal("0"),
            used_days=Decimal("0"),
        )
        db.add(balance)
        db.flush()
        return balance

    if lt and lt.tenure_based:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.hire_date:
            today = _clinic_today(db, clinic_id)
            as_of = as_of_date_for_balance_year(year, today)
            default = annual_leave_for_calendar_year(
                user.hire_date,
                year,
                as_of,
                termination_date=user.termination_date,
            )
        else:
            default = Decimal("0")

        # Refresh an existing balance when the entitlement has grown (current year only).
        if balance is not None:
            if balance.balance_days != default:
                balance.balance_days = default
                balance.updated_at = datetime.now(UTC)
                db.flush()
            return balance
    else:
        default = Decimal("0")
        if balance is not None:
            return balance

    balance = LeaveBalance(
        clinic_id=clinic_id,
        user_id=user_id,
        leave_type_id=leave_type_id,
        year=year,
        balance_days=default,
        used_days=Decimal("0"),
    )
    db.add(balance)
    db.flush()
    return balance


def has_sufficient_balance(
    db: Session,
    clinic_id: UUID,
    user_id: UUID,
    leave_type_id: UUID,
    year: int,
    days_requested: int,
) -> bool:
    lt = _get_leave_type(db, leave_type_id)
    if not lt:
        return False

    if not lt.tenure_based:
        return True

    balance = get_or_create_balance(db, clinic_id, user_id, leave_type_id, year)
    return (balance.balance_days - balance.used_days) >= _dec(days_requested)


def record_usage(
    db: Session,
    clinic_id: UUID,
    user_id: UUID,
    leave_type_id: UUID,
    year: int,
    days: int,
) -> None:
    """Track approved leave days for non-allocated leave types (usage ledger only)."""
    balance = get_or_create_balance(
        db, clinic_id, user_id, leave_type_id, year, for_usage_only=True
    )
    balance.used_days += _dec(days)
    balance.updated_at = datetime.now(UTC)


def deduct_balance(
    db: Session,
    clinic_id: UUID,
    user_id: UUID,
    leave_type_id: UUID,
    year: int,
    days: int,
) -> None:
    lt = _get_leave_type(db, leave_type_id)
    if lt and not lt.tenure_based:
        record_usage(db, clinic_id, user_id, leave_type_id, year, days)
        return
    balance = get_or_create_balance(db, clinic_id, user_id, leave_type_id, year)
    balance.used_days += _dec(days)
    balance.updated_at = datetime.now(UTC)


def restore_balance(
    db: Session,
    clinic_id: UUID,
    user_id: UUID,
    leave_type_id: UUID,
    year: int,
    days: int,
) -> None:
    balance = (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.user_id == user_id,
            LeaveBalance.leave_type_id == leave_type_id,
            LeaveBalance.year == year,
        )
        .first()
    )
    if balance:
        balance.used_days = max(Decimal("0"), balance.used_days - _dec(days))
        balance.updated_at = datetime.now(UTC)


def adjust_balance(
    db: Session,
    actor: User,
    user_id: UUID,
    leave_type_id: UUID,
    year: int,
    delta_days: float,
    reason: str,
) -> LeaveBalance:
    if not can_manage_schedules(actor):
        raise LeaveBalanceError("Insufficient permissions.")

    target = db.query(User).filter(User.id == user_id, User.clinic_id == actor.clinic_id).first()
    if not target:
        raise LeaveBalanceError("User not found.")

    lt = db.query(LeaveType).filter(
        LeaveType.id == leave_type_id, LeaveType.clinic_id == actor.clinic_id
    ).first()
    if not lt:
        raise LeaveBalanceError("Leave type not found.")
    if not lt.tenure_based:
        raise LeaveBalanceError("Only annual leave supports balance allocation adjustments.")

    balance = get_or_create_balance(db, actor.clinic_id, user_id, leave_type_id, year)

    # delta_days=0 is used purely to trigger balance initialisation; skip adjustment records.
    if _dec(delta_days) != Decimal("0"):
        new_balance = balance.balance_days + _dec(delta_days)
        if new_balance < Decimal("0"):
            raise LeaveBalanceError("Adjustment would result in a negative allocation.")
        balance.balance_days = new_balance
        balance.updated_at = datetime.now(UTC)

        adj = LeaveBalanceAdjustment(
            clinic_id=actor.clinic_id,
            leave_balance_id=balance.id,
            adjusted_by=actor.id,
            delta_days=_dec(delta_days),
            reason=reason,
        )
        db.add(adj)

        audit_service.log_action(
            db, actor.id, actor.clinic_id, AuditAction.BALANCE_ADJUSTED,
            entity_type="leave_balance",
            entity_id=str(balance.id),
            metadata={
                "user_id": str(user_id),
                "leave_type_id": str(leave_type_id),
                "year": year,
                "delta_days": delta_days,
                "reason": reason,
                "new_balance_days": float(balance.balance_days),
            },
        )

    db.commit()
    db.refresh(balance)
    return balance


def assign_default_balances(db: Session, user: User) -> None:
    """Create balance rows for tenure-based leave types when a staff member is onboarded."""
    if user.hire_date is None:
        return
    today = _clinic_today(db, user.clinic_id)
    year = today.year
    tenure_types = (
        db.query(LeaveType)
        .filter(
            LeaveType.clinic_id == user.clinic_id,
            LeaveType.active.is_(True),
            LeaveType.tenure_based.is_(True),
        )
        .all()
    )
    for lt in tenure_types:
        get_or_create_balance(db, user.clinic_id, user.id, lt.id, year)
    db.commit()


def list_balances(
    db: Session,
    actor: User,
    user_id: UUID | None = None,
    year: int | None = None,
) -> list[LeaveBalance]:
    q = db.query(LeaveBalance).filter(LeaveBalance.clinic_id == actor.clinic_id)

    if can_manage_schedules(actor):
        if user_id:
            q = q.filter(LeaveBalance.user_id == user_id)
    else:
        q = q.filter(LeaveBalance.user_id == actor.id)

    if year:
        q = q.filter(LeaveBalance.year == year)

    ordered_q = q.order_by(
        LeaveBalance.user_id, LeaveBalance.year, LeaveBalance.leave_type_id
    )
    balances = ordered_q.all()

    # Refresh formula-based balances for the current year so that anniversary
    # grants (e.g. the 15-day grant on the exact 1-year hire date) are visible
    # immediately without waiting for a leave submission to trigger the lazy
    # update in get_or_create_balance.
    today = _clinic_today(db, actor.clinic_id)
    current_year = today.year
    refreshed = False
    for b in balances:
        if b.year == current_year:
            lt = _get_leave_type(db, b.leave_type_id)
            if lt and lt.tenure_based:
                get_or_create_balance(db, b.clinic_id, b.user_id, b.leave_type_id, b.year)
                refreshed = True

    if refreshed:
        db.commit()
        balances = ordered_q.all()

    return balances
