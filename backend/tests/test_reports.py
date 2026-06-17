"""Tests for Phase 8: Reports and Exports."""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.attendance_day import AttendanceDay
from app.models.enums import AttendanceDayStatus
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from tests.conftest import login

TODAY = datetime.now(UTC).date()
YEAR = TODAY.year
MONTH = TODAY.month


def _seed_attendance(db: Session, user_id: uuid.UUID, clinic_id: uuid.UUID) -> None:
    """Create a few attendance_days rows for testing."""
    for i, status in enumerate([
        AttendanceDayStatus.COMPLETED,
        AttendanceDayStatus.COMPLETED,
        AttendanceDayStatus.ABSENT,
        AttendanceDayStatus.ON_LEAVE,
    ]):
        day = AttendanceDay(
            clinic_id=clinic_id,
            user_id=user_id,
            work_date=TODAY - timedelta(days=i + 1),
            status=status,
            worked_minutes=480 if status == AttendanceDayStatus.COMPLETED else 0,
            regular_minutes=480 if status == AttendanceDayStatus.COMPLETED else 0,
            overtime_minutes=30 if status == AttendanceDayStatus.COMPLETED else 0,
            late_minutes=0,
            early_leave_minutes=0,
            break_minutes=60,
        )
        db.add(day)
    db.commit()


def _seed_leave_balance(
    db: Session, user_id: uuid.UUID, clinic_id: uuid.UUID, leave_type_id: uuid.UUID
) -> None:
    b = LeaveBalance(
        clinic_id=clinic_id,
        user_id=user_id,
        leave_type_id=leave_type_id,
        year=YEAR,
        balance_days=15,
        used_days=5,
    )
    db.add(b)
    db.commit()


def _get_staff_id(client: TestClient) -> str:
    login(client, "staff@test.example", "StaffPass123")
    return client.get("/auth/me").json()["id"]


def _get_clinic_id(db: Session, staff_id: str) -> uuid.UUID:
    from app.models.user import User
    u = db.query(User).filter(User.id == uuid.UUID(staff_id)).first()
    assert u is not None
    return u.clinic_id


# ---------------------------------------------------------------------------
# Attendance Summary
# ---------------------------------------------------------------------------

def test_attendance_summary_empty(client: TestClient) -> None:
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/reports/attendance-summary", params={
        "start_date": str(TODAY - timedelta(days=7)),
        "end_date": str(TODAY),
    })
    assert resp.status_code == 200
    assert resp.json() == []


def test_attendance_summary_with_data(client: TestClient, db_session: Session) -> None:
    staff_id = _get_staff_id(client)
    clinic_id = _get_clinic_id(db_session, staff_id)
    _seed_attendance(db_session, uuid.UUID(staff_id), clinic_id)

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/reports/attendance-summary", params={
        "start_date": str(TODAY - timedelta(days=10)),
        "end_date": str(TODAY),
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    row = data[0]
    assert row["user_id"] == staff_id
    assert row["days_present"] == 2
    assert row["days_absent"] == 1
    assert row["days_on_leave"] == 1
    assert row["worked_hours"] == round((480 * 2) / 60, 2)
    assert row["overtime_hours"] == round((30 * 2) / 60, 2)


def test_attendance_summary_user_filter(client: TestClient, db_session: Session) -> None:
    staff_id = _get_staff_id(client)
    clinic_id = _get_clinic_id(db_session, staff_id)
    _seed_attendance(db_session, uuid.UUID(staff_id), clinic_id)

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/reports/attendance-summary", params={
        "start_date": str(TODAY - timedelta(days=10)),
        "end_date": str(TODAY),
        "user_id": staff_id,
    })
    assert resp.status_code == 200
    assert all(r["user_id"] == staff_id for r in resp.json())


def test_attendance_summary_staff_sees_only_own(client: TestClient, db_session: Session) -> None:
    staff_id = _get_staff_id(client)
    clinic_id = _get_clinic_id(db_session, staff_id)
    _seed_attendance(db_session, uuid.UUID(staff_id), clinic_id)

    login(client, "staff@test.example", "StaffPass123")
    resp = client.get("/reports/attendance-summary", params={
        "start_date": str(TODAY - timedelta(days=10)),
        "end_date": str(TODAY),
    })
    assert resp.status_code == 200
    assert all(r["user_id"] == staff_id for r in resp.json())


def test_attendance_summary_xlsx_download(client: TestClient, db_session: Session) -> None:
    staff_id = _get_staff_id(client)
    clinic_id = _get_clinic_id(db_session, staff_id)
    _seed_attendance(db_session, uuid.UUID(staff_id), clinic_id)

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/reports/attendance-summary", params={
        "start_date": str(TODAY - timedelta(days=10)),
        "end_date": str(TODAY),
        "format": "xlsx",
    })
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]
    assert len(resp.content) > 0


# ---------------------------------------------------------------------------
# Leave Summary
# ---------------------------------------------------------------------------

def test_leave_summary_empty(client: TestClient) -> None:
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/reports/leave-summary", params={"year": YEAR})
    assert resp.status_code == 200
    assert resp.json() == []


def test_leave_summary_with_data(client: TestClient, db_session: Session) -> None:
    staff_id = _get_staff_id(client)
    clinic_id = _get_clinic_id(db_session, staff_id)

    # Create a leave type and balance directly
    lt = LeaveType(
        clinic_id=clinic_id,
        name="Annual",
        default_days_per_year=15,
        requires_approval=True,
        active=True,
    )
    db_session.add(lt)
    db_session.flush()
    _seed_leave_balance(db_session, uuid.UUID(staff_id), clinic_id, lt.id)

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/reports/leave-summary", params={"year": YEAR})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    row = next(r for r in data if r["user_id"] == staff_id)
    assert row["balance_days"] == 15.0
    assert row["used_days"] == 5.0
    assert row["remaining_days"] == 10.0
    assert row["leave_type_name"] == "Annual"


def test_leave_summary_xlsx_download(client: TestClient, db_session: Session) -> None:
    staff_id = _get_staff_id(client)
    clinic_id = _get_clinic_id(db_session, staff_id)
    lt = LeaveType(
        clinic_id=clinic_id, name="Sick", default_days_per_year=10,
        requires_approval=True, active=True,
    )
    db_session.add(lt)
    db_session.flush()
    _seed_leave_balance(db_session, uuid.UUID(staff_id), clinic_id, lt.id)

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/reports/leave-summary", params={"year": YEAR, "format": "xlsx"})
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]


# ---------------------------------------------------------------------------
# Monthly Detail
# ---------------------------------------------------------------------------

def test_monthly_detail_empty(client: TestClient) -> None:
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/reports/monthly-detail", params={"year": YEAR, "month": MONTH})
    assert resp.status_code == 200
    assert resp.json() == []


def test_monthly_detail_with_data(client: TestClient, db_session: Session) -> None:
    staff_id = _get_staff_id(client)
    clinic_id = _get_clinic_id(db_session, staff_id)
    _seed_attendance(db_session, uuid.UUID(staff_id), clinic_id)

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/reports/monthly-detail", params={"year": YEAR, "month": MONTH})
    assert resp.status_code == 200
    # Rows may exist if seeded dates fall in current month
    for row in resp.json():
        assert "work_date" in row
        assert "user_name" in row
        assert "status" in row
        assert "worked_hours" in row


def test_monthly_detail_xlsx_download(client: TestClient, db_session: Session) -> None:
    staff_id = _get_staff_id(client)
    clinic_id = _get_clinic_id(db_session, staff_id)
    _seed_attendance(db_session, uuid.UUID(staff_id), clinic_id)

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/reports/monthly-detail", params={
        "year": YEAR, "month": MONTH, "format": "xlsx",
    })
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]


def test_monthly_detail_invalid_month(client: TestClient) -> None:
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/reports/monthly-detail", params={"year": YEAR, "month": 13})
    assert resp.status_code == 422


def test_monthly_detail_staff_sees_only_own(client: TestClient, db_session: Session) -> None:
    staff_id = _get_staff_id(client)
    clinic_id = _get_clinic_id(db_session, staff_id)
    _seed_attendance(db_session, uuid.UUID(staff_id), clinic_id)

    login(client, "staff@test.example", "StaffPass123")
    resp = client.get("/reports/monthly-detail", params={"year": YEAR, "month": MONTH})
    assert resp.status_code == 200
    assert all(r["user_id"] == staff_id for r in resp.json())
