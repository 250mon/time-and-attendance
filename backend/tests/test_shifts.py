from fastapi.testclient import TestClient

from tests.conftest import login

MORNING_SHIFT = {
    "name": "Morning",
    "start_time": "09:00:00",
    "end_time": "18:00:00",
    "break_minutes": 60,
    "crosses_midnight": False,
}


def _create_shift(client: TestClient) -> dict:
    login(client, "admin@test.example", "AdminPass123")
    response = client.post("/shifts", json=MORNING_SHIFT)
    assert response.status_code == 201
    return response.json()


def test_all_roles_can_list_shifts(client: TestClient) -> None:
    _create_shift(client)

    login(client, "staff@test.example", "StaffPass123")
    response = client.get("/shifts")

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_manager_can_create_shift(client: TestClient) -> None:
    login(client, "manager@test.example", "ManagerPass123")

    response = client.post("/shifts", json=MORNING_SHIFT)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Morning"
    assert body["start_time"] == "09:00:00"
    assert body["break_minutes"] == 60
    assert body["active"] is True


def test_staff_cannot_create_shift(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    response = client.post("/shifts", json=MORNING_SHIFT)

    assert response.status_code == 403


def test_admin_can_update_shift(client: TestClient) -> None:
    shift = _create_shift(client)

    response = client.patch(f"/shifts/{shift['id']}", json={"name": "Day Shift", "break_minutes": 30})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Day Shift"
    assert body["break_minutes"] == 30
    assert body["start_time"] == "09:00:00"  # unchanged


def test_shift_update_ignores_unset_fields(client: TestClient) -> None:
    shift = _create_shift(client)

    response = client.patch(f"/shifts/{shift['id']}", json={"name": "Updated"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Updated"
    assert body["end_time"] == "18:00:00"  # unchanged
    assert body["crosses_midnight"] is False  # unchanged


def test_staff_cannot_update_shift(client: TestClient) -> None:
    shift = _create_shift(client)

    login(client, "staff@test.example", "StaffPass123")
    response = client.patch(f"/shifts/{shift['id']}", json={"name": "Hacked"})

    assert response.status_code == 403


def test_admin_can_deactivate_shift(client: TestClient) -> None:
    shift = _create_shift(client)

    response = client.delete(f"/shifts/{shift['id']}")

    assert response.status_code == 200
    assert response.json()["active"] is False


def test_staff_cannot_deactivate_shift(client: TestClient) -> None:
    shift = _create_shift(client)

    login(client, "staff@test.example", "StaffPass123")
    response = client.delete(f"/shifts/{shift['id']}")

    assert response.status_code == 403
