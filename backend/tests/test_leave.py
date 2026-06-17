"""Tests for Phase 6: Leave Management."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import login

TODAY = datetime.now(UTC).date()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()
LAST_WEEK_START = (TODAY - timedelta(days=7)).isoformat()
LAST_WEEK_END = (TODAY - timedelta(days=5)).isoformat()
NEXT_WEEK_START = (TODAY + timedelta(days=7)).isoformat()
NEXT_WEEK_END = (TODAY + timedelta(days=9)).isoformat()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_leave_type(client: TestClient, name: str = "Annual Leave", days: int = 15) -> dict:
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post("/leave/types", json={"name": name, "default_days_per_year": days})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _submit_request(
    client: TestClient,
    leave_type_id: str,
    start: str = NEXT_WEEK_START,
    end: str = NEXT_WEEK_END,
    reason: str | None = "Vacation",
) -> dict:
    resp = client.post("/leave/requests", json={
        "leave_type_id": leave_type_id,
        "start_date": start,
        "end_date": end,
        "reason": reason,
    })
    return resp


# ---------------------------------------------------------------------------
# Leave Types
# ---------------------------------------------------------------------------

def test_manager_can_create_leave_type(client: TestClient) -> None:
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post("/leave/types", json={"name": "Sick Leave", "default_days_per_year": 10})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Sick Leave"
    assert resp.json()["default_days_per_year"] == 10
    assert resp.json()["requires_approval"] is True
    assert resp.json()["active"] is True


def test_staff_cannot_create_leave_type(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    resp = client.post("/leave/types", json={"name": "Test"})
    assert resp.status_code == 403


def test_list_leave_types_accessible_to_all(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    resp = client.get("/leave/types")
    assert resp.status_code == 200
    assert any(t["id"] == lt["id"] for t in resp.json())


def test_update_leave_type(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.patch(f"/leave/types/{lt['id']}", json={"default_days_per_year": 20})
    assert resp.status_code == 200
    assert resp.json()["default_days_per_year"] == 20
    assert resp.json()["name"] == lt["name"]  # unchanged


def test_deactivate_leave_type(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.delete(f"/leave/types/{lt['id']}")
    assert resp.status_code == 200
    assert resp.json()["active"] is False


def test_inactive_type_excluded_from_list(client: TestClient) -> None:
    lt = _create_leave_type(client, name="Temp Leave")
    login(client, "manager@test.example", "ManagerPass123")
    client.delete(f"/leave/types/{lt['id']}")

    resp = client.get("/leave/types")
    assert not any(t["id"] == lt["id"] for t in resp.json())

    resp2 = client.get("/leave/types?include_inactive=true")
    assert any(t["id"] == lt["id"] for t in resp2.json())


def test_leave_types_require_auth(client: TestClient) -> None:
    resp = client.get("/leave/types")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Leave Requests – creation
# ---------------------------------------------------------------------------

def test_staff_can_submit_leave_request(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    resp = _submit_request(client, lt["id"])
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "PENDING"
    assert body["total_days"] == 3
    assert body["reviewer_id"] is None


def test_leave_request_requires_auth(client: TestClient) -> None:
    resp = client.post("/leave/requests", json={
        "leave_type_id": str(uuid4()), "start_date": NEXT_WEEK_START, "end_date": NEXT_WEEK_END,
    })
    assert resp.status_code == 401


def test_end_date_before_start_rejected(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    resp = _submit_request(client, lt["id"], start=NEXT_WEEK_END, end=NEXT_WEEK_START)
    assert resp.status_code == 422


def test_overlapping_request_rejected(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    _submit_request(client, lt["id"])

    # Overlapping range
    overlap_start = (TODAY + timedelta(days=8)).isoformat()
    overlap_end = (TODAY + timedelta(days=10)).isoformat()
    resp = _submit_request(client, lt["id"], start=overlap_start, end=overlap_end)
    assert resp.status_code == 400
    assert "overlapping" in resp.json()["detail"].lower()


def test_non_overlapping_same_user_allowed(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    _submit_request(client, lt["id"])  # next week

    # Different period (2 weeks from now)
    start2 = (TODAY + timedelta(days=14)).isoformat()
    end2 = (TODAY + timedelta(days=16)).isoformat()
    resp = _submit_request(client, lt["id"], start=start2, end=end2)
    assert resp.status_code == 201


def test_inactive_leave_type_cannot_be_requested(client: TestClient) -> None:
    lt = _create_leave_type(client, name="Obsolete Leave")
    login(client, "manager@test.example", "ManagerPass123")
    client.delete(f"/leave/types/{lt['id']}")

    login(client, "staff@test.example", "StaffPass123")
    resp = _submit_request(client, lt["id"])
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Leave Requests – visibility
# ---------------------------------------------------------------------------

def test_staff_sees_own_requests(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    _submit_request(client, lt["id"])
    resp = client.get("/leave/requests")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_manager_sees_all_requests(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    _submit_request(client, lt["id"])
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/leave/requests")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_filter_by_status(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    _submit_request(client, lt["id"])
    resp = client.get("/leave/requests?status=PENDING")
    assert all(r["status"] == "PENDING" for r in resp.json())
    resp2 = client.get("/leave/requests?status=APPROVED")
    assert len(resp2.json()) == 0


# ---------------------------------------------------------------------------
# Leave Requests – approval / rejection
# ---------------------------------------------------------------------------

def test_manager_can_approve(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    creation = _submit_request(client, lt["id"])
    req_id = creation.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post(f"/leave/requests/{req_id}/approve", json={})
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"
    assert resp.json()["reviewer_id"] is not None


def test_staff_cannot_approve(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    creation = _submit_request(client, lt["id"])
    resp = client.post(f"/leave/requests/{creation.json()['id']}/approve", json={})
    assert resp.status_code == 403


def test_cannot_approve_own_request(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "manager@test.example", "ManagerPass123")
    creation = _submit_request(client, lt["id"])
    resp = client.post(f"/leave/requests/{creation.json()['id']}/approve", json={})
    assert resp.status_code == 400
    assert "own" in resp.json()["detail"].lower()


def test_manager_can_reject_with_note(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    creation = _submit_request(client, lt["id"])
    req_id = creation.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post(f"/leave/requests/{req_id}/reject", json={"reviewer_note": "Clinic is busy"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"
    assert resp.json()["reviewer_note"] == "Clinic is busy"


def test_cannot_approve_already_rejected(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    creation = _submit_request(client, lt["id"])
    req_id = creation.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    client.post(f"/leave/requests/{req_id}/reject", json={})
    resp = client.post(f"/leave/requests/{req_id}/approve", json={})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Leave Requests – cancellation
# ---------------------------------------------------------------------------

def test_staff_can_cancel_pending(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    creation = _submit_request(client, lt["id"])
    resp = client.delete(f"/leave/requests/{creation.json()['id']}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"


def test_cannot_cancel_approved(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    creation = _submit_request(client, lt["id"])
    req_id = creation.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    client.post(f"/leave/requests/{req_id}/approve", json={})

    login(client, "staff@test.example", "StaffPass123")
    resp = client.delete(f"/leave/requests/{req_id}")
    assert resp.status_code == 400


def test_after_cancel_overlap_allowed(client: TestClient) -> None:
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")
    creation = _submit_request(client, lt["id"])
    client.delete(f"/leave/requests/{creation.json()['id']}")

    resp = _submit_request(client, lt["id"])
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Integration: approved leave → attendance_day ON_LEAVE
# ---------------------------------------------------------------------------

def test_approved_leave_sets_on_leave_status(client: TestClient, db_session: Session) -> None:
    """Approving leave for a past date recalculates attendance_day to ON_LEAVE."""
    lt = _create_leave_type(client)
    login(client, "staff@test.example", "StaffPass123")

    # Request leave for last week (past)
    creation = _submit_request(client, lt["id"], start=LAST_WEEK_START, end=LAST_WEEK_START)
    req_id = creation.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    client.post(f"/leave/requests/{req_id}/approve", json={})

    # Check that the staff member's attendance_day for that date is ON_LEAVE
    login(client, "staff@test.example", "StaffPass123")
    resp = client.get(f"/attendance/days?start_date={LAST_WEEK_START}&end_date={LAST_WEEK_START}")
    assert resp.status_code == 200
    days = resp.json()
    assert len(days) == 1
    assert days[0]["status"] == "ON_LEAVE"
