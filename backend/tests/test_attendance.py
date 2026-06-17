from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.conftest import login


def test_staff_can_clock_in(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    response = client.post("/attendance/clock-in")

    assert response.status_code == 201
    body = response.json()
    assert body["punch_type"] == "CLOCK_IN"
    assert body["source"] == "WEB"


def test_staff_cannot_clock_in_twice(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")

    response = client.post("/attendance/clock-in")

    assert response.status_code == 400
    assert "Already clocked in" in response.json()["detail"]


def test_staff_can_clock_out_after_clock_in(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")

    response = client.post("/attendance/clock-out")

    assert response.status_code == 201
    assert response.json()["punch_type"] == "CLOCK_OUT"


def test_staff_cannot_clock_out_without_clock_in(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    response = client.post("/attendance/clock-out")

    assert response.status_code == 400
    assert "No active clock-in" in response.json()["detail"]


def test_full_clock_cycle_allows_re_clock_in(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")
    client.post("/attendance/clock-out")

    response = client.post("/attendance/clock-in")

    assert response.status_code == 201


def test_get_today_not_clocked_in(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    response = client.get("/attendance/today")

    assert response.status_code == 200
    body = response.json()
    assert body["is_clocked_in"] is False
    assert body["punches"] == []
    assert body["last_punch"] is None


def test_get_today_reflects_clock_in(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")

    response = client.get("/attendance/today")

    assert response.status_code == 200
    body = response.json()
    assert body["is_clocked_in"] is True
    assert len(body["punches"]) == 1
    assert body["last_punch"]["punch_type"] == "CLOCK_IN"


def test_get_today_reflects_clock_out(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")
    client.post("/attendance/clock-out")

    response = client.get("/attendance/today")

    body = response.json()
    assert body["is_clocked_in"] is False
    assert len(body["punches"]) == 2


def test_get_my_punches_returns_own_records(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")
    client.post("/attendance/clock-out")

    response = client.get("/attendance/me")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_my_punches_unauthenticated(client: TestClient) -> None:
    response = client.get("/attendance/me")
    assert response.status_code == 401


def test_staff_cannot_access_daily_view(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    response = client.get("/attendance/daily")

    assert response.status_code == 403


def test_manager_can_access_daily_view(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")

    login(client, "manager@test.example", "ManagerPass123")
    response = client.get("/attendance/daily")

    assert response.status_code == 200
    entries = response.json()
    staff_entry = next((e for e in entries if e["user_name"] == "Staff User"), None)
    assert staff_entry is not None
    assert staff_entry["is_clocked_in"] is True


def test_staff_cannot_access_monthly_view(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    response = client.get("/attendance/monthly")

    assert response.status_code == 403


def test_manager_can_access_monthly_view(client: TestClient, db_session: Session) -> None:
    login(client, "staff@test.example", "StaffPass123")
    client.post("/attendance/clock-in")

    login(client, "manager@test.example", "ManagerPass123")
    response = client.get("/attendance/monthly")

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_today_requires_auth(client: TestClient) -> None:
    response = client.get("/attendance/today")
    assert response.status_code == 401
