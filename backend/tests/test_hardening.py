"""Security headers and global exception handler tests."""
from unittest.mock import patch

from fastapi.testclient import TestClient


def test_security_headers_present(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "permissions-policy" in response.headers


def test_request_id_header_present(client: TestClient) -> None:
    response = client.get("/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


def test_request_id_unique_per_request(client: TestClient) -> None:
    r1 = client.get("/health")
    r2 = client.get("/health")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


def test_unhandled_exception_returns_500_without_traceback(db_session) -> None:
    from app.db.session import get_db
    from app.main import app

    @app.get("/test-crash")
    def crash():
        raise RuntimeError("boom")

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        # raise_server_exceptions=False makes TestClient return the 500 response
        # instead of propagating the exception into the test.
        with TestClient(app, raise_server_exceptions=False) as safe_client:
            response = safe_client.get("/test-crash")
        assert response.status_code == 500
        body = response.json()
        assert body == {"detail": "Internal server error"}
        assert "boom" not in str(body)
    finally:
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/test-crash"]
        app.dependency_overrides.clear()


def test_unauthenticated_request_returns_401(client: TestClient) -> None:
    response = client.get("/staff")
    assert response.status_code == 401


def test_health_endpoint_public(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
