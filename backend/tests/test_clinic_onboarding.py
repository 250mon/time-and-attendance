"""MT-5: POST /clinics (bootstrap) — clinic onboarding API tests."""

import pytest
from fastapi.testclient import TestClient

import app.core.config as config_module

BOOTSTRAP_SECRET = "test-bootstrap-secret-xyz"
HEADERS = {"X-Bootstrap-Secret": BOOTSTRAP_SECRET}

VALID_PAYLOAD = {
    "name": "Hangang Dental Clinic",
    "slug": "hangang-dental",
    "timezone": "Asia/Seoul",
    "address": "123 Riverside Rd, Seoul",
    "owner_name": "Dr. Park",
    "owner_email": "park@hangang.example",
    "owner_password": "Secure123!",
}


@pytest.fixture(autouse=True)
def enable_bootstrap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module.settings, "clinic_bootstrap_secret", BOOTSTRAP_SECRET)


class TestCreateClinic:
    def test_success_creates_clinic_owner_and_leave_types(self, client: TestClient) -> None:
        resp = client.post("/clinics", json=VALID_PAYLOAD, headers=HEADERS)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["name"] == "Hangang Dental Clinic"
        assert body["slug"] == "hangang-dental"
        assert body["status"] == "ACTIVE"
        assert body["timezone"] == "Asia/Seoul"
        assert "id" in body

    def test_owner_can_log_in_after_creation(self, client: TestClient) -> None:
        client.post("/clinics", json=VALID_PAYLOAD, headers=HEADERS)
        resp = client.post(
            "/auth/login",
            json={
                "email": VALID_PAYLOAD["owner_email"],
                "password": VALID_PAYLOAD["owner_password"],
                "clinic_slug": VALID_PAYLOAD["slug"],
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["role"] == "OWNER"
        assert body["clinic"]["slug"] == "hangang-dental"

    def test_duplicate_slug_returns_409(self, client: TestClient) -> None:
        client.post("/clinics", json=VALID_PAYLOAD, headers=HEADERS)
        resp = client.post("/clinics", json=VALID_PAYLOAD, headers=HEADERS)
        assert resp.status_code == 409

    def test_wrong_secret_returns_401(self, client: TestClient) -> None:
        resp = client.post(
            "/clinics",
            json=VALID_PAYLOAD,
            headers={"X-Bootstrap-Secret": "wrong-secret"},
        )
        assert resp.status_code == 401

    def test_missing_secret_returns_401(self, client: TestClient) -> None:
        resp = client.post("/clinics", json=VALID_PAYLOAD)
        assert resp.status_code == 401

    def test_bootstrap_disabled_returns_503(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(config_module.settings, "clinic_bootstrap_secret", "")
        resp = client.post("/clinics", json=VALID_PAYLOAD, headers=HEADERS)
        assert resp.status_code == 503

    def test_invalid_timezone_returns_422(self, client: TestClient) -> None:
        bad = {**VALID_PAYLOAD, "slug": "tz-test-clinic", "timezone": "Not/ATimezone"}
        resp = client.post("/clinics", json=bad, headers=HEADERS)
        assert resp.status_code == 422

    def test_reserved_slug_returns_422(self, client: TestClient) -> None:
        bad = {**VALID_PAYLOAD, "slug": "admin"}
        resp = client.post("/clinics", json=bad, headers=HEADERS)
        assert resp.status_code == 422

    def test_invalid_slug_format_returns_422(self, client: TestClient) -> None:
        bad = {**VALID_PAYLOAD, "slug": "-bad-slug-"}
        resp = client.post("/clinics", json=bad, headers=HEADERS)
        assert resp.status_code == 422

    def test_short_password_returns_422(self, client: TestClient) -> None:
        bad = {**VALID_PAYLOAD, "slug": "pw-test-clinic", "owner_password": "short"}
        resp = client.post("/clinics", json=bad, headers=HEADERS)
        assert resp.status_code == 422

    def test_new_clinic_isolated_from_existing(self, client: TestClient) -> None:
        """Staff of the new clinic must not appear in the existing test clinic's staff list."""
        from tests.conftest import login

        client.post("/clinics", json=VALID_PAYLOAD, headers=HEADERS)

        # Log in as the original test admin
        login(client, "admin@test.example", "AdminPass123")
        resp = client.get("/staff")
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert VALID_PAYLOAD["owner_email"] not in emails
