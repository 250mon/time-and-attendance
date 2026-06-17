"""Tests for Phase 9: Monthly Closing and Audit Log."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.attendance_day import AttendanceDay
from app.models.enums import AttendanceDayStatus
from tests.conftest import login

TODAY = datetime.now(UTC).date()
YEAR = TODAY.year
MONTH = TODAY.month
PREV_MONTH = MONTH - 1 if MONTH > 1 else 12
PREV_YEAR = YEAR if MONTH > 1 else YEAR - 1


def _get_ids(client: TestClient, db: Session):
    login(client, "staff@test.example", "StaffPass123")
    staff_id = client.get("/auth/me").json()["id"]
    from app.models.user import User
    u = db.query(User).filter(User.id == uuid.UUID(staff_id)).first()
    assert u
    return staff_id, u.clinic_id


def _seed_day(db: Session, clinic_id: uuid.UUID, user_id: uuid.UUID, work_date) -> AttendanceDay:
    d = AttendanceDay(
        clinic_id=clinic_id,
        user_id=user_id,
        work_date=work_date,
        status=AttendanceDayStatus.COMPLETED,
        worked_minutes=480,
        regular_minutes=480,
        overtime_minutes=0,
        late_minutes=0,
        early_leave_minutes=0,
        break_minutes=60,
    )
    db.add(d)
    db.commit()
    return d


# ---------------------------------------------------------------------------
# Monthly Closing — lock / unlock
# ---------------------------------------------------------------------------

def test_admin_can_lock_month(client: TestClient) -> None:
    login(client, "admin@test.example", "AdminPass123")
    resp = client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/lock")
    assert resp.status_code == 200
    data = resp.json()
    assert data["year"] == PREV_YEAR
    assert data["month"] == PREV_MONTH
    assert data["is_locked"] is True
    assert data["locked_by"] is not None


def test_manager_cannot_lock_month(client: TestClient) -> None:
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/lock")
    assert resp.status_code == 403


def test_staff_cannot_lock_month(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    resp = client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/lock")
    assert resp.status_code == 403


def test_lock_already_locked_month(client: TestClient) -> None:
    login(client, "admin@test.example", "AdminPass123")
    client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/lock")
    resp = client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/lock")
    assert resp.status_code == 409


def test_admin_can_unlock_month(client: TestClient) -> None:
    login(client, "admin@test.example", "AdminPass123")
    client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/lock")
    resp = client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/unlock")
    assert resp.status_code == 200
    assert resp.json()["is_locked"] is False
    assert resp.json()["unlocked_by"] is not None


def test_unlock_not_locked_month(client: TestClient) -> None:
    login(client, "admin@test.example", "AdminPass123")
    resp = client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/unlock")
    assert resp.status_code == 409


def test_list_closings(client: TestClient) -> None:
    login(client, "admin@test.example", "AdminPass123")
    client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/lock")

    resp = client.get("/closings")
    assert resp.status_code == 200
    data = resp.json()
    assert any(c["year"] == PREV_YEAR and c["month"] == PREV_MONTH for c in data)


def test_list_closings_year_filter(client: TestClient) -> None:
    login(client, "admin@test.example", "AdminPass123")
    client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/lock")

    resp = client.get("/closings", params={"year": PREV_YEAR})
    assert resp.status_code == 200
    assert all(c["year"] == PREV_YEAR for c in resp.json())


def test_lock_sets_attendance_days_locked(client: TestClient, db_session: Session) -> None:
    staff_id, clinic_id = _get_ids(client, db_session)
    # Use a past-month date
    past_date = TODAY.replace(day=1) - timedelta(days=1)  # last day of prev month
    day = _seed_day(db_session, clinic_id, uuid.UUID(staff_id), past_date)

    login(client, "admin@test.example", "AdminPass123")
    client.post(f"/closings/{past_date.year}/{past_date.month}/lock")

    db_session.refresh(day)
    assert day.is_locked is True


def test_unlock_clears_attendance_days_locked(client: TestClient, db_session: Session) -> None:
    staff_id, clinic_id = _get_ids(client, db_session)
    past_date = TODAY.replace(day=1) - timedelta(days=1)
    day = _seed_day(db_session, clinic_id, uuid.UUID(staff_id), past_date)

    login(client, "admin@test.example", "AdminPass123")
    client.post(f"/closings/{past_date.year}/{past_date.month}/lock")
    client.post(f"/closings/{past_date.year}/{past_date.month}/unlock")

    db_session.refresh(day)
    assert day.is_locked is False


def test_locked_month_blocks_correction_submission(client: TestClient, db_session: Session) -> None:
    staff_id, clinic_id = _get_ids(client, db_session)
    past_date = TODAY.replace(day=1) - timedelta(days=1)

    login(client, "admin@test.example", "AdminPass123")
    client.post(f"/closings/{past_date.year}/{past_date.month}/lock")

    login(client, "staff@test.example", "StaffPass123")
    resp = client.post("/attendance/corrections", json={
        "work_date": str(past_date),
        "corrected_clock_in": "09:00",
        "reason": "Test correction",
    })
    assert resp.status_code == 400
    assert "locked" in resp.json()["detail"].lower()


def test_locked_month_blocks_correction_approval(client: TestClient, db_session: Session) -> None:
    staff_id, clinic_id = _get_ids(client, db_session)
    # Work date far enough in the past to submit a correction
    past_date = TODAY - timedelta(days=40)

    # Submit correction first (month not yet locked)
    login(client, "staff@test.example", "StaffPass123")
    resp = client.post("/attendance/corrections", json={
        "work_date": str(past_date),
        "corrected_clock_in": "09:00",
        "reason": "Test correction",
    })
    assert resp.status_code == 201
    correction_id = resp.json()["id"]

    # Lock that month
    login(client, "admin@test.example", "AdminPass123")
    client.post(f"/closings/{past_date.year}/{past_date.month}/lock")

    # Try to approve → should be blocked
    resp = client.post(f"/attendance/corrections/{correction_id}/approve", json={})
    assert resp.status_code == 400
    assert "locked" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

def test_audit_log_created_on_month_lock(client: TestClient) -> None:
    login(client, "admin@test.example", "AdminPass123")
    client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/lock")

    resp = client.get("/audit-logs", params={"action": "MONTH_LOCKED"})
    assert resp.status_code == 200
    logs = resp.json()
    assert any(
        log["action"] == "MONTH_LOCKED"
        and log["extra_data"]["year"] == PREV_YEAR
        and log["extra_data"]["month"] == PREV_MONTH
        for log in logs
    )


def test_audit_log_created_on_month_unlock(client: TestClient) -> None:
    login(client, "admin@test.example", "AdminPass123")
    client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/lock")
    client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/unlock")

    resp = client.get("/audit-logs", params={"action": "MONTH_UNLOCKED"})
    assert resp.status_code == 200
    assert any(log["action"] == "MONTH_UNLOCKED" for log in resp.json())


def test_audit_log_created_on_correction_approve(client: TestClient, db_session: Session) -> None:
    staff_id, _ = _get_ids(client, db_session)
    past_date = TODAY - timedelta(days=5)

    login(client, "staff@test.example", "StaffPass123")
    resp = client.post("/attendance/corrections", json={
        "work_date": str(past_date),
        "corrected_clock_in": "09:00",
        "reason": "Late start",
    })
    assert resp.status_code == 201
    corr_id = resp.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    client.post(f"/attendance/corrections/{corr_id}/approve", json={})

    resp = client.get("/audit-logs", params={"action": "CORRECTION_APPROVED"})
    assert resp.status_code == 200
    assert any(log["entity_id"] == corr_id for log in resp.json())


def test_audit_log_created_on_leave_approve(client: TestClient) -> None:
    # Create leave type
    login(client, "manager@test.example", "ManagerPass123")
    lt = client.post("/leave/types", json={"name": "Annual", "default_days_per_year": 15}).json()

    login(client, "staff@test.example", "StaffPass123")
    future_start = (TODAY + timedelta(days=7)).isoformat()
    future_end = (TODAY + timedelta(days=9)).isoformat()
    req = client.post("/leave/requests", json={
        "leave_type_id": lt["id"],
        "start_date": future_start,
        "end_date": future_end,
    }).json()

    login(client, "manager@test.example", "ManagerPass123")
    client.post(f"/leave/requests/{req['id']}/approve", json={})

    resp = client.get("/audit-logs", params={"action": "LEAVE_APPROVED"})
    assert resp.status_code == 200
    assert any(log["entity_id"] == req["id"] for log in resp.json())


def test_audit_log_balance_adjusted(client: TestClient) -> None:
    login(client, "manager@test.example", "ManagerPass123")
    lt = client.post("/leave/types", json={"name": "Flex", "default_days_per_year": 10}).json()

    login(client, "staff@test.example", "StaffPass123")
    resp = client.get("/auth/me")
    staff_id = resp.json()["id"]
    # Submit a request to trigger balance creation
    future_start = (TODAY + timedelta(days=14)).isoformat()
    future_end = (TODAY + timedelta(days=15)).isoformat()
    client.post("/leave/requests", json={
        "leave_type_id": lt["id"],
        "start_date": future_start,
        "end_date": future_end,
    })

    login(client, "manager@test.example", "ManagerPass123")
    client.post("/leave/balances/adjust", json={
        "user_id": staff_id,
        "leave_type_id": lt["id"],
        "year": YEAR,
        "delta_days": 3,
        "reason": "Performance award",
    })

    resp = client.get("/audit-logs", params={"action": "BALANCE_ADJUSTED"})
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_audit_log_pagination(client: TestClient) -> None:
    login(client, "admin@test.example", "AdminPass123")
    # Generate a few log entries
    for m in range(1, 4):
        client.post(f"/closings/{PREV_YEAR}/{m}/lock")

    resp = client.get("/audit-logs", params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    assert len(resp.json()) <= 2


def test_audit_log_includes_actor_name(client: TestClient) -> None:
    login(client, "admin@test.example", "AdminPass123")
    client.post(f"/closings/{PREV_YEAR}/{PREV_MONTH}/lock")

    resp = client.get("/audit-logs", params={"action": "MONTH_LOCKED"})
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) > 0
    assert logs[0]["actor_name"] == "Admin User"
