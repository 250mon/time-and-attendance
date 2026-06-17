"""Tests for Phase 5: Attendance Correction Workflow."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import login

YESTERDAY = (datetime.now(UTC).date() - timedelta(days=1)).isoformat()
TWO_DAYS_AGO = (datetime.now(UTC).date() - timedelta(days=2)).isoformat()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_correction(
    client: TestClient,
    work_date: str = YESTERDAY,
    clock_in: str | None = "09:00",
    clock_out: str | None = "18:00",
    reason: str = "Forgot to clock in",
) -> dict:
    body: dict = {"work_date": work_date, "reason": reason}
    if clock_in is not None:
        body["corrected_clock_in"] = clock_in
    if clock_out is not None:
        body["corrected_clock_out"] = clock_out
    resp = client.post("/attendance/corrections", json=body)
    return resp


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


def test_staff_can_submit_correction(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    # First clock in/out so there's an attendance_day to attach to
    client.post("/attendance/clock-in")
    client.post("/attendance/clock-out")

    resp = _create_correction(client)

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "PENDING"
    assert body["corrected_clock_in"] is not None
    assert body["corrected_clock_out"] is not None
    assert body["reviewer_id"] is None


def test_correction_requires_auth(client: TestClient) -> None:
    resp = client.post("/attendance/corrections", json={
        "work_date": YESTERDAY, "corrected_clock_in": "09:00", "reason": "test",
    })
    assert resp.status_code == 401


def test_correction_rejects_future_date(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    tomorrow = (datetime.now(UTC).date() + timedelta(days=1)).isoformat()

    resp = _create_correction(client, work_date=tomorrow)

    assert resp.status_code == 400
    assert "past" in resp.json()["detail"].lower()


def test_correction_requires_at_least_one_time(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    resp = client.post("/attendance/corrections", json={
        "work_date": YESTERDAY,
        "reason": "Test",
    })
    assert resp.status_code == 422


def test_correction_rejects_clock_out_before_clock_in(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    resp = _create_correction(client, clock_in="18:00", clock_out="09:00")
    assert resp.status_code == 400


def test_duplicate_pending_correction_rejected(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    _create_correction(client)

    resp = _create_correction(client)

    assert resp.status_code == 400
    assert "pending" in resp.json()["detail"].lower()


def test_correction_only_clock_in(client: TestClient) -> None:
    """Single corrected time is allowed."""
    login(client, "staff@test.example", "StaffPass123")
    resp = _create_correction(client, clock_in="09:30", clock_out=None)
    assert resp.status_code == 201
    assert resp.json()["corrected_clock_out"] is None


# ---------------------------------------------------------------------------
# Listing & visibility
# ---------------------------------------------------------------------------


def test_staff_sees_own_corrections(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    _create_correction(client)

    resp = client.get("/attendance/corrections")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_staff_cannot_see_others_corrections(client: TestClient, db_session: Session) -> None:
    login(client, "staff@test.example", "StaffPass123")
    _create_correction(client)

    login(client, "manager@test.example", "ManagerPass123")
    from app.core.security import hash_password
    from app.models.enums import EmploymentType, UserRole, UserStatus
    from app.models.user import User
    from uuid import uuid4

    other = User(
        id=uuid4(),
        clinic_id=db_session.query(User).filter(User.email == "staff@test.example").first().clinic_id,
        name="Other Staff",
        email="other2@test.example",
        password_hash=hash_password("OtherPass123"),
        role=UserRole.STAFF,
        employment_type=EmploymentType.FULL_TIME,
        status=UserStatus.ACTIVE,
    )
    db_session.add(other)
    db_session.commit()

    login(client, "other2@test.example", "OtherPass123")
    resp = client.get("/attendance/corrections")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_manager_sees_all_corrections(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    _create_correction(client)

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/attendance/corrections")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_filter_by_status(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    _create_correction(client)

    resp = client.get("/attendance/corrections?status=PENDING")
    assert resp.status_code == 200
    assert all(r["status"] == "PENDING" for r in resp.json())

    resp2 = client.get("/attendance/corrections?status=APPROVED")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 0


# ---------------------------------------------------------------------------
# Approval
# ---------------------------------------------------------------------------


def test_manager_can_approve(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    creation = _create_correction(client)
    correction_id = creation.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post(f"/attendance/corrections/{correction_id}/approve", json={})

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "APPROVED"
    assert body["reviewer_id"] is not None
    assert body["reviewed_at"] is not None


def test_staff_cannot_approve(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    creation = _create_correction(client)
    correction_id = creation.json()["id"]

    resp = client.post(f"/attendance/corrections/{correction_id}/approve", json={})

    assert resp.status_code == 403


def test_cannot_approve_own_correction(client: TestClient) -> None:
    """A manager cannot approve a correction they themselves submitted."""
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post("/attendance/corrections", json={
        "work_date": YESTERDAY,
        "corrected_clock_in": "09:00",
        "reason": "I was late",
    })
    correction_id = resp.json()["id"]

    resp2 = client.post(f"/attendance/corrections/{correction_id}/approve", json={})
    assert resp2.status_code == 400
    assert "own" in resp2.json()["detail"].lower()


def test_approve_triggers_recalculation(client: TestClient) -> None:
    """After approval, GET /attendance/days should reflect corrected times."""
    login(client, "staff@test.example", "StaffPass123")
    creation = _create_correction(client, clock_in="09:00", clock_out="18:00")
    correction_id = creation.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    client.post(f"/attendance/corrections/{correction_id}/approve", json={})

    # Read staff's attendance days via manager
    from app.models.user import User

    staff_id = None
    login(client, "staff@test.example", "StaffPass123")
    days_resp = client.get(f"/attendance/days?start_date={YESTERDAY}&end_date={YESTERDAY}")
    assert days_resp.status_code == 200
    days = days_resp.json()
    assert len(days) == 1
    assert days[0]["status"] == "COMPLETED"
    assert days[0]["actual_clock_in"] is not None
    assert days[0]["actual_clock_out"] is not None


def test_approve_with_reviewer_note(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    creation = _create_correction(client)
    correction_id = creation.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post(
        f"/attendance/corrections/{correction_id}/approve",
        json={"reviewer_note": "Confirmed via entry log"},
    )
    assert resp.status_code == 200
    assert resp.json()["reviewer_note"] == "Confirmed via entry log"


# ---------------------------------------------------------------------------
# Rejection
# ---------------------------------------------------------------------------


def test_manager_can_reject(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    creation = _create_correction(client)
    correction_id = creation.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post(
        f"/attendance/corrections/{correction_id}/reject",
        json={"reviewer_note": "No evidence provided"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"
    assert resp.json()["reviewer_note"] == "No evidence provided"


def test_cannot_approve_already_rejected(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    creation = _create_correction(client)
    correction_id = creation.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    client.post(f"/attendance/corrections/{correction_id}/reject", json={})

    resp = client.post(f"/attendance/corrections/{correction_id}/approve", json={})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------


def test_staff_can_cancel_own_pending(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    creation = _create_correction(client)
    correction_id = creation.json()["id"]

    resp = client.delete(f"/attendance/corrections/{correction_id}")

    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"


def test_staff_cannot_cancel_others(client: TestClient, db_session: Session) -> None:
    from app.core.security import hash_password
    from app.models.enums import EmploymentType, UserRole, UserStatus
    from app.models.user import User
    from uuid import uuid4

    clinic_id = db_session.query(User).filter(User.email == "staff@test.example").first().clinic_id
    other = User(
        id=uuid4(), clinic_id=clinic_id, name="Staff B",
        email="staffb@test.example", password_hash=hash_password("StaffBPass123"),
        role=UserRole.STAFF, employment_type=EmploymentType.FULL_TIME, status=UserStatus.ACTIVE,
    )
    db_session.add(other)
    db_session.commit()

    login(client, "staff@test.example", "StaffPass123")
    creation = _create_correction(client)
    correction_id = creation.json()["id"]

    login(client, "staffb@test.example", "StaffBPass123")
    resp = client.delete(f"/attendance/corrections/{correction_id}")
    assert resp.status_code in (403, 404)


def test_cannot_cancel_approved(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    creation = _create_correction(client)
    correction_id = creation.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    client.post(f"/attendance/corrections/{correction_id}/approve", json={})

    login(client, "staff@test.example", "StaffPass123")
    resp = client.delete(f"/attendance/corrections/{correction_id}")
    assert resp.status_code == 400


def test_after_cancel_new_correction_allowed(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    creation = _create_correction(client)
    correction_id = creation.json()["id"]

    client.delete(f"/attendance/corrections/{correction_id}")

    resp = _create_correction(client)
    assert resp.status_code == 201
