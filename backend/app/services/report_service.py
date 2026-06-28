import io
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

import openpyxl
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from app.core.clinic_time import clinic_tz
from app.core.permissions import can_manage_schedules
from app.models.attendance_day import AttendanceDay
from app.models.clinic import Clinic
from app.models.enums import AttendanceDayStatus
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.user import User
from app.schemas.report import AttendanceSummaryRow, LeaveSummaryRow, MonthlyDetailRow


def _to_clinic_tz(dt: datetime | None, tz: ZoneInfo) -> datetime | None:
    if dt is None:
        return None
    return dt.astimezone(tz)


# ── Attendance Summary ────────────────────────────────────────────────────────

def attendance_summary(
    db: Session,
    actor: User,
    start_date: date,
    end_date: date,
    user_id: UUID | None = None,
) -> list[AttendanceSummaryRow]:
    q = db.query(AttendanceDay).filter(
        AttendanceDay.clinic_id == actor.clinic_id,
        AttendanceDay.work_date >= start_date,
        AttendanceDay.work_date <= end_date,
    )
    if can_manage_schedules(actor):
        if user_id:
            q = q.filter(AttendanceDay.user_id == user_id)
    else:
        q = q.filter(AttendanceDay.user_id == actor.id)

    days = q.all()

    agg: dict[UUID, dict] = defaultdict(lambda: {
        "total_records": 0, "days_present": 0, "days_absent": 0,
        "days_on_leave": 0, "days_holiday": 0,
        "worked_minutes": 0, "overtime_minutes": 0,
        "late_minutes": 0, "early_leave_minutes": 0,
    })
    for d in days:
        a = agg[d.user_id]
        a["total_records"] += 1
        if d.status in (AttendanceDayStatus.COMPLETED, AttendanceDayStatus.WORKING):
            a["days_present"] += 1
        elif d.status == AttendanceDayStatus.ABSENT:
            a["days_absent"] += 1
        elif d.status == AttendanceDayStatus.ON_LEAVE:
            a["days_on_leave"] += 1
        elif d.status == AttendanceDayStatus.HOLIDAY:
            a["days_holiday"] += 1
        a["worked_minutes"] += d.worked_minutes
        a["overtime_minutes"] += d.overtime_minutes
        a["late_minutes"] += d.late_minutes
        a["early_leave_minutes"] += d.early_leave_minutes

    user_ids = list(agg.keys())
    users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()}

    result = []
    for uid, data in sorted(agg.items(), key=lambda x: users.get(x[0], User()).name or ""):
        u = users.get(uid)
        if not u:
            continue
        result.append(AttendanceSummaryRow(
            user_id=uid,
            user_name=u.name,
            user_email=u.email,
            total_records=data["total_records"],
            days_present=data["days_present"],
            days_absent=data["days_absent"],
            days_on_leave=data["days_on_leave"],
            days_holiday=data["days_holiday"],
            worked_hours=round(data["worked_minutes"] / 60, 2),
            overtime_hours=round(data["overtime_minutes"] / 60, 2),
            late_minutes=data["late_minutes"],
            early_leave_minutes=data["early_leave_minutes"],
        ))
    return result


def attendance_summary_xlsx(rows: list[AttendanceSummaryRow], start_date: date, end_date: date) -> bytes:
    headers = [
        "Staff Name", "Email", "Total Records",
        "Days Present", "Days Absent", "Days On Leave", "Days Holiday",
        "Worked Hours", "Overtime Hours", "Late (min)", "Early Leave (min)",
    ]
    data_rows = [
        [
            r.user_name, r.user_email, r.total_records,
            r.days_present, r.days_absent, r.days_on_leave, r.days_holiday,
            r.worked_hours, r.overtime_hours, r.late_minutes, r.early_leave_minutes,
        ]
        for r in rows
    ]
    title = f"Attendance Summary {start_date} to {end_date}"
    return _make_xlsx(title, headers, data_rows)


# ── Leave Summary ─────────────────────────────────────────────────────────────

def leave_summary(
    db: Session,
    actor: User,
    year: int,
    user_id: UUID | None = None,
) -> list[LeaveSummaryRow]:
    q = (
        db.query(LeaveBalance, User, LeaveType)
        .join(User, User.id == LeaveBalance.user_id)
        .join(LeaveType, LeaveType.id == LeaveBalance.leave_type_id)
        .filter(LeaveBalance.clinic_id == actor.clinic_id, LeaveBalance.year == year)
    )
    if can_manage_schedules(actor):
        if user_id:
            q = q.filter(LeaveBalance.user_id == user_id)
    else:
        q = q.filter(LeaveBalance.user_id == actor.id)

    rows = q.order_by(User.name, LeaveType.name).all()
    return [
        LeaveSummaryRow(
            user_id=bal.user_id,
            user_name=user.name,
            leave_type_id=bal.leave_type_id,
            leave_type_name=lt.name,
            year=bal.year,
            balance_days=float(bal.balance_days),
            used_days=float(bal.used_days),
            remaining_days=float(bal.balance_days - bal.used_days),
        )
        for bal, user, lt in rows
    ]


def leave_summary_xlsx(rows: list[LeaveSummaryRow], year: int) -> bytes:
    headers = ["Staff Name", "Leave Type", "Year", "Allocated (days)", "Used (days)", "Remaining (days)"]
    data_rows = [
        [r.user_name, r.leave_type_name, r.year, r.balance_days, r.used_days, r.remaining_days]
        for r in rows
    ]
    return _make_xlsx(f"Leave Summary {year}", headers, data_rows)


# ── Monthly Detail ────────────────────────────────────────────────────────────

def monthly_detail(
    db: Session,
    actor: User,
    year: int,
    month: int,
    user_id: UUID | None = None,
) -> list[MonthlyDetailRow]:
    _, last_day = monthrange(year, month)
    start = date(year, month, 1)
    end = date(year, month, last_day)

    q = db.query(AttendanceDay, User).join(User, User.id == AttendanceDay.user_id).filter(
        AttendanceDay.clinic_id == actor.clinic_id,
        AttendanceDay.work_date >= start,
        AttendanceDay.work_date <= end,
    )
    if can_manage_schedules(actor):
        if user_id:
            q = q.filter(AttendanceDay.user_id == user_id)
    else:
        q = q.filter(AttendanceDay.user_id == actor.id)

    clinic = db.get(Clinic, actor.clinic_id)
    tz = clinic_tz(clinic.timezone if clinic else None)

    rows = q.order_by(User.name, AttendanceDay.work_date).all()
    return [
        MonthlyDetailRow(
            work_date=d.work_date,
            user_id=d.user_id,
            user_name=u.name,
            status=d.status,
            actual_clock_in=_to_clinic_tz(d.actual_clock_in, tz),
            actual_clock_out=_to_clinic_tz(d.actual_clock_out, tz),
            worked_minutes=d.worked_minutes,
            worked_hours=round(d.worked_minutes / 60, 2),
            overtime_minutes=d.overtime_minutes,
            late_minutes=d.late_minutes,
            early_leave_minutes=d.early_leave_minutes,
            is_locked=d.is_locked,
        )
        for d, u in rows
    ]


def monthly_detail_xlsx(rows: list[MonthlyDetailRow], year: int, month: int) -> bytes:
    def _fmt(dt: datetime | None) -> str:
        return dt.strftime("%H:%M") if dt else ""

    headers = [
        "Date", "Staff", "Status", "Clock In", "Clock Out",
        "Worked (min)", "Worked (h)", "Overtime (min)", "Late (min)", "Early Leave (min)", "Locked",
    ]
    data_rows = [
        [
            r.work_date.strftime("%Y-%m-%d"), r.user_name, r.status.value,
            _fmt(r.actual_clock_in), _fmt(r.actual_clock_out),
            r.worked_minutes, r.worked_hours, r.overtime_minutes,
            r.late_minutes, r.early_leave_minutes, "Yes" if r.is_locked else "No",
        ]
        for r in rows
    ]
    import calendar
    month_name = calendar.month_name[month]
    return _make_xlsx(f"Monthly Detail {month_name} {year}", headers, data_rows)


# ── Excel helper ──────────────────────────────────────────────────────────────

def _make_xlsx(sheet_title: str, headers: list[str], rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]  # Excel sheet name limit

    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for row in rows:
        ws.append(row)

    # Auto-width columns
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=0)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
