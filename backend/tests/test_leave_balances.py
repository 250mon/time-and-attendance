"""Tests for Phase 7: Leave Balance Engine."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from tests.conftest import login

TODAY = datetime.now(UTC).date()
# 3-day range (inclusive)
NEXT_WEEK_START = (TODAY + timedelta(days=7)).isoformat()
NEXT_WEEK_END = (TODAY + timedelta(days=9)).isoformat()
# 5-day range
NEXT_MONTH_START = (TODAY + timedelta(days=30)).isoformat()
NEXT_MONTH_END = (TODAY + timedelta(days=34)).isoformat()
YEAR = TODAY.year


def _create_leave_type(client: TestClient, name: str = "Annual Leave", days: int = 15) -> dict:
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post("/leave/types", json={"name": name, "default_days_per_year": days})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _submit_request(client: TestClient, leave_type_id: str, start: str, end: str) -> dict:
    resp = client.post("/leave/requests", json={
        "leave_type_id": leave_type_id,
        "start_date": start,
        "end_date": end,
    })
    return resp.json()


def _get_balances(client: TestClient, user_id: str | None = None, year: int | None = None) -> list:
    params: dict = {}
    if user_id:
        params["user_id"] = user_id
    if year:
        params["year"] = year
    resp = client.get("/leave/balances", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Balance deduction / restoration (non-annual: usage tracking, not allocation)
# ---------------------------------------------------------------------------

def test_exact_balance_is_allowed(client: TestClient) -> None:
    lt = _create_leave_type(client, name="Exact Balance Leave", days=3)
    login(client, "staff@test.example", "StaffPass123")

    resp = client.post("/leave/requests", json={
        "leave_type_id": lt["id"],
        "start_date": NEXT_WEEK_START,
        "end_date": NEXT_WEEK_END,
    })
    assert resp.status_code == 201


def test_manager_cancel_approved_leave_restores_usage(client: TestClient) -> None:
    lt = _create_leave_type(client, days=15)
    login(client, "staff@test.example", "StaffPass123")
    resp = client.get("/auth/me")
    staff_id = resp.json()["id"]
    req = _submit_request(client, lt["id"], NEXT_WEEK_START, NEXT_WEEK_END)

    login(client, "manager@test.example", "ManagerPass123")
    client.post(f"/leave/requests/{req['id']}/approve", json={})

    # Verify usage recorded after approval
    login(client, "staff@test.example", "StaffPass123")
    balances = _get_balances(client, user_id=staff_id, year=YEAR)
    b = next(x for x in balances if x["leave_type_id"] == lt["id"])
    assert b["used_days"] == 3.0

    # Manager cancels approved leave
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.delete(f"/leave/requests/{req['id']}")
    assert resp.status_code == 200

    # Usage restored to zero
    login(client, "staff@test.example", "StaffPass123")
    balances = _get_balances(client, user_id=staff_id, year=YEAR)
    b = next(x for x in balances if x["leave_type_id"] == lt["id"])
    assert b["used_days"] == 0.0


# ---------------------------------------------------------------------------
# Manual adjustment
# ---------------------------------------------------------------------------

def test_staff_cannot_adjust_balance(client: TestClient) -> None:
    lt = _create_leave_type(client, days=15)
    login(client, "staff@test.example", "StaffPass123")
    resp = client.get("/auth/me")
    staff_id = resp.json()["id"]

    resp = client.post("/leave/balances/adjust", json={
        "user_id": staff_id,
        "leave_type_id": lt["id"],
        "year": YEAR,
        "delta_days": 10,
        "reason": "Self grant",
    })
    assert resp.status_code == 403


def test_adjust_nonexistent_user_returns_404(client: TestClient) -> None:
    import uuid
    lt = _create_leave_type(client, days=15)
    login(client, "manager@test.example", "ManagerPass123")

    resp = client.post("/leave/balances/adjust", json={
        "user_id": str(uuid.uuid4()),
        "leave_type_id": lt["id"],
        "year": YEAR,
        "delta_days": 5,
        "reason": "Test",
    })
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------

def test_list_balances_staff_sees_only_own(client: TestClient) -> None:
    lt = _create_leave_type(client, days=15)
    login(client, "staff@test.example", "StaffPass123")
    resp = client.get("/auth/me")
    staff_id = resp.json()["id"]
    _submit_request(client, lt["id"], NEXT_WEEK_START, NEXT_WEEK_END)

    resp = client.get("/leave/balances")
    assert resp.status_code == 200
    data = resp.json()
    assert all(b["user_id"] == staff_id for b in data)


def test_list_balances_manager_can_filter_by_user(client: TestClient) -> None:
    lt = _create_leave_type(client, days=15)
    login(client, "staff@test.example", "StaffPass123")
    resp = client.get("/auth/me")
    staff_id = resp.json()["id"]
    _submit_request(client, lt["id"], NEXT_WEEK_START, NEXT_WEEK_END)

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.get("/leave/balances", params={"user_id": staff_id})
    assert resp.status_code == 200
    data = resp.json()
    assert all(b["user_id"] == staff_id for b in data)


def test_list_balances_year_filter(client: TestClient) -> None:
    lt = _create_leave_type(client, days=15)
    login(client, "staff@test.example", "StaffPass123")
    resp = client.get("/auth/me")
    staff_id = resp.json()["id"]
    _submit_request(client, lt["id"], NEXT_WEEK_START, NEXT_WEEK_END)

    resp = client.get("/leave/balances", params={"year": YEAR, "user_id": staff_id})
    assert resp.status_code == 200
    data = resp.json()
    assert all(b["year"] == YEAR for b in data)

    # Different year should return no results (balance only created for current year)
    resp = client.get("/leave/balances", params={"year": YEAR + 1, "user_id": staff_id})
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Non-annual leave: per-request cap and usage tracking
# ---------------------------------------------------------------------------

def test_non_annual_leave_warns_when_exceeding_per_request_max(client: TestClient) -> None:
    """Non-annual types warn (but allow) when a request exceeds the per-request maximum."""
    lt = _create_leave_type(client, name="Sick Leave", days=2)
    login(client, "staff@test.example", "StaffPass123")

    resp = client.post("/leave/requests", json={
        "leave_type_id": lt["id"],
        "start_date": NEXT_WEEK_START,
        "end_date": NEXT_WEEK_END,
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["exceeds_per_request_max"] is True
    assert data["max_days_per_request"] == 2
    assert data["policy_warning"] is not None
    assert "per request" in data["policy_warning"].lower()


def test_non_annual_leave_allows_request_within_per_request_max(client: TestClient) -> None:
    lt = _create_leave_type(client, name="Sick Leave", days=3)
    login(client, "staff@test.example", "StaffPass123")

    resp = client.post("/leave/requests", json={
        "leave_type_id": lt["id"],
        "start_date": NEXT_WEEK_START,
        "end_date": NEXT_WEEK_END,
    })
    assert resp.status_code == 201, resp.text


def test_non_annual_multiple_requests_not_capped_yearly(client: TestClient) -> None:
    """Per-request max does not limit total usage across multiple approved requests."""
    lt = _create_leave_type(client, name="Sick Leave", days=2)
    login(client, "staff@test.example", "StaffPass123")

    req1 = _submit_request(client, lt["id"], NEXT_WEEK_START, NEXT_WEEK_START)

    login(client, "manager@test.example", "ManagerPass123")
    client.post(f"/leave/requests/{req1['id']}/approve", json={})

    login(client, "staff@test.example", "StaffPass123")
    resp = client.post("/leave/requests", json={
        "leave_type_id": lt["id"],
        "start_date": NEXT_MONTH_START,
        "end_date": NEXT_MONTH_START,
    })
    assert resp.status_code == 201, resp.text


def test_non_annual_unlimited_when_no_max(client: TestClient) -> None:
    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post("/leave/types", json={"name": "Unlimited Leave"})
    assert resp.status_code == 201
    lt = resp.json()

    login(client, "staff@test.example", "StaffPass123")
    resp = client.post("/leave/requests", json={
        "leave_type_id": lt["id"],
        "start_date": NEXT_WEEK_START,
        "end_date": NEXT_MONTH_END,
    })
    assert resp.status_code == 201, resp.text


def test_non_annual_adjust_balance_rejected(client: TestClient) -> None:
    lt = _create_leave_type(client, name="Sick Leave", days=5)
    login(client, "staff@test.example", "StaffPass123")
    resp = client.get("/auth/me")
    staff_id = resp.json()["id"]

    login(client, "manager@test.example", "ManagerPass123")
    resp = client.post("/leave/balances/adjust", json={
        "user_id": staff_id,
        "leave_type_id": lt["id"],
        "year": YEAR,
        "delta_days": 5,
        "reason": "Should not work",
    })
    assert resp.status_code == 400
    assert "annual leave" in resp.json()["detail"].lower()


def test_non_annual_approve_records_usage_only(client: TestClient) -> None:
    lt = _create_leave_type(client, name="Family Care", days=10)
    login(client, "staff@test.example", "StaffPass123")
    resp = client.get("/auth/me")
    staff_id = resp.json()["id"]
    req = _submit_request(client, lt["id"], NEXT_WEEK_START, NEXT_WEEK_END)

    login(client, "manager@test.example", "ManagerPass123")
    client.post(f"/leave/requests/{req['id']}/approve", json={})

    login(client, "staff@test.example", "StaffPass123")
    balances = _get_balances(client, user_id=staff_id, year=YEAR)
    sick_balance = next(b for b in balances if b["leave_type_id"] == lt["id"])
    assert sick_balance["balance_days"] == 0.0
    assert sick_balance["used_days"] == 3.0
