from fastapi.testclient import TestClient

from tests.conftest import login


def test_login_success(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "admin@test.example", "password": "AdminPass123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "admin@test.example"
    assert body["role"] == "ADMIN"
    assert "access_token" in response.cookies


def test_login_failure(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "admin@test.example", "password": "WrongPassword123"},
    )

    assert response.status_code == 401


def test_inactive_user_cannot_login(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "inactive@test.example", "password": "InactivePass123"},
    )

    assert response.status_code == 401


def test_auth_me_requires_login(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_auth_me_returns_current_user(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "staff@test.example"


def test_logout_clears_session(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 204

    me_response = client.get("/auth/me")
    assert me_response.status_code == 401


def test_change_password_success(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    response = client.post(
        "/auth/change-password",
        json={"current_password": "StaffPass123", "new_password": "NewPass456!"},
    )

    assert response.status_code == 204

    client.post("/auth/logout")
    login(client, "staff@test.example", "NewPass456!")
    assert client.get("/auth/me").status_code == 200


def test_change_password_wrong_current(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    response = client.post(
        "/auth/change-password",
        json={"current_password": "WrongPass123", "new_password": "NewPass456!"},
    )

    assert response.status_code == 400


def test_change_password_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/auth/change-password",
        json={"current_password": "StaffPass123", "new_password": "NewPass456!"},
    )

    assert response.status_code == 401


def test_change_password_rejects_short_new_password(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    response = client.post(
        "/auth/change-password",
        json={"current_password": "StaffPass123", "new_password": "short"},
    )

    assert response.status_code == 422
