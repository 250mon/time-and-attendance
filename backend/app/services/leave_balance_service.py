from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
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


def _compute_lazy_carryover(
    db: Session,
    lt: "LeaveType | None",
    user_id: "UUID",
    year: int,
) -> Decimal:
    """Return carryover amount from year-1 if the leave type allows it."""
    if lt is None or not lt.allow_carryover:
        return Decimal("0")
    prior = (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.user_id == user_id,
            LeaveBalance.leave_type_id == lt.id,
            LeaveBalance.year == year - 1,
        )
        .first()
    )
    if prior is None:
        return Decimal("0")
    remaining = prior.balance_days + prior.carryover_days - prior.used_days
    if remaining <= Decimal("0"):
        return Decimal("0")
    if lt.carryover_max_days is not None:
        remaining = min(remaining, Decimal(str(lt.carryover_max_days)))
    return remaining


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
            carryover_days=_compute_lazy_carryover(db, lt, user_id, year),
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
        carryover_days=_compute_lazy_carryover(db, lt, user_id, year),
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
    return (balance.balance_days + balance.carryover_days - balance.used_days) >= _dec(days_requested)


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
    balance = get_or_create_balance(
        db, actor.clinic_id, user_id, leave_type_id, year,
        for_usage_only=not lt.tenure_based,
    )

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


def carry_forward_year(db: Session, actor: User, from_year: int) -> int:
    """Carry unused days from from_year into from_year+1 for all staff in the clinic.

    Only processes leave types with allow_carryover=True.  Idempotent: calling
    again overwrites the previously written carryover_days with the current
    remaining from from_year (safe to re-run before any from_year+1 leave is used).

    Returns the number of balance rows updated.
    """
    if not can_manage_schedules(actor):
        raise LeaveBalanceError("Insufficient permissions.")

    to_year = from_year + 1

    carry_types = (
        db.query(LeaveType)
        .filter(
            LeaveType.clinic_id == actor.clinic_id,
            LeaveType.allow_carryover.is_(True),
        )
        .all()
    )
    if not carry_types:
        return 0

    carry_map = {lt.id: lt for lt in carry_types}

    from_balances = (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.clinic_id == actor.clinic_id,
            LeaveBalance.leave_type_id.in_(carry_map.keys()),
            LeaveBalance.year == from_year,
        )
        .all()
    )

    count = 0
    for from_bal in from_balances:
        remaining = from_bal.balance_days + from_bal.carryover_days - from_bal.used_days
        if remaining <= Decimal("0"):
            continue

        lt = carry_map[from_bal.leave_type_id]
        carry_amount = remaining
        if lt.carryover_max_days is not None:
            carry_amount = min(carry_amount, Decimal(str(lt.carryover_max_days)))

        to_bal = (
            db.query(LeaveBalance)
            .filter(
                LeaveBalance.user_id == from_bal.user_id,
                LeaveBalance.leave_type_id == from_bal.leave_type_id,
                LeaveBalance.year == to_year,
            )
            .first()
        )

        if to_bal is None:
            to_bal = LeaveBalance(
                clinic_id=actor.clinic_id,
                user_id=from_bal.user_id,
                leave_type_id=from_bal.leave_type_id,
                year=to_year,
                balance_days=Decimal("0"),
                carryover_days=carry_amount,
                used_days=Decimal("0"),
            )
            db.add(to_bal)
        else:
            to_bal.carryover_days = carry_amount
            to_bal.updated_at = datetime.now(UTC)

        count += 1

    db.commit()
    return count


def assign_default_balances(db: Session, user: User) -> None:
    """Create balance rows for tenure-based leave types when a staff member is onboarded.

    Creates one row per year from hire year to current year in chronological order
    so that _compute_lazy_carryover can chain correctly (each year's row finds the
    prior year's row when computing carryover_days).
    """
    if user.hire_date is None:
        return
    today = _clinic_today(db, user.clinic_id)
    current_year = today.year
    hire_year = user.hire_date.year
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
        for yr in range(hire_year, current_year + 1):
            get_or_create_balance(db, user.clinic_id, user.id, lt.id, yr)
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

    today = _clinic_today(db, actor.clinic_id)
    current_year = today.year
    target_year = year if year else current_year
    need_commit = False

    # ── Seed missing rows, filling multi-year gaps ───────────────────────────
    # A staff member may have balance rows in earlier years but nothing for
    # target_year yet (e.g. onboarded mid-season, or never submitted leave in
    # the new year).  A one-year-back look doesn't help when the gap spans
    # multiple years.  Instead: find the latest existing year per (user,
    # leave_type) pair that is strictly before target_year, then fill forward
    # year-by-year so _compute_lazy_carryover can chain at each step.
    if target_year <= current_year:
        latest_q = (
            db.query(
                LeaveBalance.user_id,
                LeaveBalance.leave_type_id,
                LeaveBalance.clinic_id,
                func.max(LeaveBalance.year).label("latest_year"),
            )
            .filter(
                LeaveBalance.clinic_id == actor.clinic_id,
                LeaveBalance.year < target_year,
            )
        )
        if not can_manage_schedules(actor):
            latest_q = latest_q.filter(LeaveBalance.user_id == actor.id)
        elif user_id:
            latest_q = latest_q.filter(LeaveBalance.user_id == user_id)
        latest_q = latest_q.group_by(
            LeaveBalance.user_id, LeaveBalance.leave_type_id, LeaveBalance.clinic_id
        )

        existing_pairs = {(b.user_id, b.leave_type_id) for b in balances}
        for row in latest_q.all():
            if (row.user_id, row.leave_type_id) not in existing_pairs:
                for yr in range(row.latest_year + 1, target_year + 1):
                    get_or_create_balance(
                        db, row.clinic_id, row.user_id, row.leave_type_id, yr
                    )
                need_commit = True

    # ── Refresh and patch existing rows ──────────────────────────────────────
    for b in balances:
        lt = _get_leave_type(db, b.leave_type_id)
        if lt is None:
            continue

        # Refresh tenure-based entitlement for the current year so anniversary
        # grants appear immediately without waiting for a leave submission.
        if lt.tenure_based and b.year == current_year:
            get_or_create_balance(db, b.clinic_id, b.user_id, b.leave_type_id, b.year)
            need_commit = True

        # Patch any existing row where carryover was not set yet (e.g. allow_carryover
        # was enabled on the leave type after the row was already created).
        if lt.allow_carryover and b.carryover_days == Decimal("0"):
            carry = _compute_lazy_carryover(db, lt, b.user_id, b.year)
            if carry > Decimal("0"):
                b.carryover_days = carry
                b.updated_at = datetime.now(UTC)
                need_commit = True

    if need_commit:
        db.commit()
        balances = ordered_q.all()

    return balances


def list_adjustments(
    db: Session,
    actor: User,
    balance_id: UUID,
) -> list["LeaveBalanceAdjustment"]:
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.id == balance_id,
        LeaveBalance.clinic_id == actor.clinic_id,
    ).first()
    if balance is None:
        raise LeaveBalanceError("Balance not found.")
    if not can_manage_schedules(actor) and balance.user_id != actor.id:
        raise LeaveBalanceError("Insufficient permissions.")
    return (
        db.query(LeaveBalanceAdjustment)
        .filter(LeaveBalanceAdjustment.leave_balance_id == balance_id)
        .order_by(LeaveBalanceAdjustment.created_at.desc())
        .all()
    )
