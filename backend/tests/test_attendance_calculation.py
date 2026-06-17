"""Tests for Phase 4: Attendance Calculation Engine."""

from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.attendance_day import AttendanceDay
from app.models.attendance_punch import AttendancePunch
from app.models.enums import AttendanceDayStatus, PunchSource, PunchType, ScheduleStatus
from app.models.staff_schedule import StaffSchedule
from app.services.attendance_calculation_service import recalculate_attendance_day
from tests.conftest import login


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_staff_user(db: Session):
    from app.models.user import User

    return db.query(User).filter(User.email == "staff@test.example").first()


def _get_clinic(db: Session):
    from app.models.clinic import Clinic

    return db.query(Clinic).first()


def _insert_punch(db: Session, user, punch_type: PunchType, punched_at: datetime) -> AttendancePunch:
    p = AttendancePunch(
        clinic_id=user.clinic_id,
        user_id=user.id,
        punch_type=punch_type,
        punched_at=punched_at,
        source=PunchSource.WEB,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _insert_schedule(
    db: Session,
    user,
    work_date: date,
    start: time,
    end: time,
    break_minutes: int = 0,
    status: ScheduleStatus = ScheduleStatus.SCHEDULED,
) -> StaffSchedule:
    s = StaffSchedule(
        clinic_id=user.clinic_id,
        user_id=user.id,
        work_date=work_date,
        scheduled_start=start,
        scheduled_end=end,
        scheduled_break_minutes=break_minutes,
        status=status,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ---------------------------------------------------------------------------
# API-level tests
# ---------------------------------------------------------------------------


def test_clock_in_creates_working_attendance_day(client: TestClient, db_session: Session) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")

    response = client.get("/attendance/days")

    assert response.status_code == 200
    days = response.json()
    assert len(days) == 1
    assert days[0]["status"] == "WORKING"
    assert days[0]["actual_clock_in"] is not None
    assert days[0]["actual_clock_out"] is None
    assert days[0]["worked_minutes"] == 0


def test_clock_out_updates_to_completed(client: TestClient, db_session: Session) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")
    client.post("/attendance/clock-out")

    response = client.get("/attendance/days")

    assert response.status_code == 200
    days = response.json()
    assert len(days) == 1
    assert days[0]["status"] == "COMPLETED"
    assert days[0]["actual_clock_out"] is not None
    assert days[0]["worked_minutes"] >= 0


def test_get_days_unauthenticated(client: TestClient) -> None:
    response = client.get("/attendance/days")
    assert response.status_code == 401


def test_get_days_staff_sees_only_own(client: TestClient, db_session: Session) -> None:
    # Staff clocks in
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")

    # Manager queries for own records (none)
    login(client, "manager@test.example", "ManagerPass123")
    response = client.get("/attendance/days")

    assert response.status_code == 200
    assert len(response.json()) == 0


def test_manager_can_query_specific_user(client: TestClient, db_session: Session) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")
    staff_user = _get_staff_user(db_session)

    login(client, "manager@test.example", "ManagerPass123")
    response = client.get(f"/attendance/days?user_id={staff_user.id}")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "WORKING"


def test_staff_cannot_query_other_user(client: TestClient, db_session: Session) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")

    # Another staff user tries to query the first
    from app.models.user import User
    from app.core.security import hash_password
    from app.models.enums import EmploymentType, UserRole, UserStatus

    other = User(
        id=uuid4(),
        clinic_id=_get_staff_user(db_session).clinic_id,
        name="Other Staff",
        email="other@test.example",
        password_hash=hash_password("OtherPass123"),
        role=UserRole.STAFF,
        employment_type=EmploymentType.FULL_TIME,
        status=UserStatus.ACTIVE,
    )
    db_session.add(other)
    db_session.commit()

    login(client, "other@test.example", "OtherPass123")
    staff = _get_staff_user(db_session)
    response = client.get(f"/attendance/days?user_id={staff.id}")

    assert response.status_code == 403


def test_days_date_range_filter(client: TestClient, db_session: Session) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")
    client.post("/attendance/clock-out")

    from datetime import UTC, datetime as dt

    tomorrow = (dt.now(UTC).date() + timedelta(days=1)).isoformat()
    response = client.get(f"/attendance/days?start_date={tomorrow}&end_date={tomorrow}")

    assert response.status_code == 200
    assert len(response.json()) == 0


# ---------------------------------------------------------------------------
# Unit-level tests against the calculation service directly
# ---------------------------------------------------------------------------


def test_recalculate_absent_for_past_scheduled_day(db_session: Session) -> None:
    staff = _get_staff_user(db_session)
    past_date = datetime.now(UTC).date() - timedelta(days=3)

    _insert_schedule(db_session, staff, past_date, time(9, 0), time(18, 0), break_minutes=60)

    day = recalculate_attendance_day(db_session, staff.clinic_id, staff.id, past_date)

    assert day.status == AttendanceDayStatus.ABSENT
    assert day.worked_minutes == 0
    assert day.late_minutes == 0


def test_recalculate_holiday_status(db_session: Session) -> None:
    staff = _get_staff_user(db_session)
    past_date = datetime.now(UTC).date() - timedelta(days=2)

    _insert_schedule(
        db_session, staff, past_date, time(9, 0), time(18, 0),
        status=ScheduleStatus.HOLIDAY,
    )

    day = recalculate_attendance_day(db_session, staff.clinic_id, staff.id, past_date)

    assert day.status == AttendanceDayStatus.HOLIDAY


def test_recalculate_late_minutes(db_session: Session) -> None:
    """Clock in 30 minutes after scheduled start → late_minutes == 30."""
    from zoneinfo import ZoneInfo

    staff = _get_staff_user(db_session)
    work_date = datetime.now(UTC).date() - timedelta(days=1)
    tz = ZoneInfo("Asia/Seoul")

    _insert_schedule(db_session, staff, work_date, time(9, 0), time(18, 0), break_minutes=60)

    # Clock in 30 min late (09:30 KST)
    clock_in_kst = datetime(work_date.year, work_date.month, work_date.day, 9, 30, tzinfo=tz)
    clock_out_kst = datetime(work_date.year, work_date.month, work_date.day, 18, 0, tzinfo=tz)

    _insert_punch(db_session, staff, PunchType.CLOCK_IN, clock_in_kst.astimezone(UTC))
    _insert_punch(db_session, staff, PunchType.CLOCK_OUT, clock_out_kst.astimezone(UTC))

    day = recalculate_attendance_day(db_session, staff.clinic_id, staff.id, work_date)

    assert day.status == AttendanceDayStatus.COMPLETED
    assert day.late_minutes == 30
    assert day.early_leave_minutes == 0


def test_recalculate_early_leave_minutes(db_session: Session) -> None:
    """Clock out 45 minutes before scheduled end → early_leave_minutes == 45."""
    from zoneinfo import ZoneInfo

    staff = _get_staff_user(db_session)
    work_date = datetime.now(UTC).date() - timedelta(days=1)
    tz = ZoneInfo("Asia/Seoul")

    _insert_schedule(db_session, staff, work_date, time(9, 0), time(18, 0), break_minutes=60)

    clock_in_kst = datetime(work_date.year, work_date.month, work_date.day, 9, 0, tzinfo=tz)
    clock_out_kst = datetime(work_date.year, work_date.month, work_date.day, 17, 15, tzinfo=tz)

    _insert_punch(db_session, staff, PunchType.CLOCK_IN, clock_in_kst.astimezone(UTC))
    _insert_punch(db_session, staff, PunchType.CLOCK_OUT, clock_out_kst.astimezone(UTC))

    day = recalculate_attendance_day(db_session, staff.clinic_id, staff.id, work_date)

    assert day.early_leave_minutes == 45


def test_recalculate_overtime(db_session: Session) -> None:
    """Work 2 hours beyond scheduled end → overtime_minutes == 120."""
    from zoneinfo import ZoneInfo

    staff = _get_staff_user(db_session)
    work_date = datetime.now(UTC).date() - timedelta(days=1)
    tz = ZoneInfo("Asia/Seoul")

    _insert_schedule(db_session, staff, work_date, time(9, 0), time(18, 0), break_minutes=60)

    clock_in_kst = datetime(work_date.year, work_date.month, work_date.day, 9, 0, tzinfo=tz)
    clock_out_kst = datetime(work_date.year, work_date.month, work_date.day, 20, 0, tzinfo=tz)

    _insert_punch(db_session, staff, PunchType.CLOCK_IN, clock_in_kst.astimezone(UTC))
    _insert_punch(db_session, staff, PunchType.CLOCK_OUT, clock_out_kst.astimezone(UTC))

    day = recalculate_attendance_day(db_session, staff.clinic_id, staff.id, work_date)

    # Scheduled net = 9h - 1h break = 8h = 480 min; worked = 11h - 1h = 10h = 600 min
    assert day.regular_minutes == 480
    assert day.overtime_minutes == 120


def test_recalculate_is_idempotent(db_session: Session) -> None:
    """Calling recalculate twice with the same data produces the same result."""
    staff = _get_staff_user(db_session)
    work_date = datetime.now(UTC).date()

    _insert_punch(db_session, staff, PunchType.CLOCK_IN, datetime.now(UTC))

    day1 = recalculate_attendance_day(db_session, staff.clinic_id, staff.id, work_date)
    day2 = recalculate_attendance_day(db_session, staff.clinic_id, staff.id, work_date)

    assert day1.id == day2.id
    assert day2.status == AttendanceDayStatus.WORKING


def test_recalculate_locked_day_is_not_modified(db_session: Session) -> None:
    staff = _get_staff_user(db_session)
    work_date = datetime.now(UTC).date() - timedelta(days=1)

    day = AttendanceDay(
        clinic_id=staff.clinic_id,
        user_id=staff.id,
        work_date=work_date,
        status=AttendanceDayStatus.COMPLETED,
        worked_minutes=480,
        regular_minutes=480,
        overtime_minutes=0,
        late_minutes=0,
        early_leave_minutes=0,
        break_minutes=60,
        is_locked=True,
    )
    db_session.add(day)
    db_session.commit()

    # Add a punch that would normally change the record
    _insert_punch(db_session, staff, PunchType.CLOCK_IN, datetime.now(UTC) - timedelta(hours=2))

    result = recalculate_attendance_day(db_session, staff.clinic_id, staff.id, work_date)

    # Should be unchanged because locked
    assert result.id == day.id
    assert result.worked_minutes == 480
    assert result.status == AttendanceDayStatus.COMPLETED
