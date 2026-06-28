"""MT-1 tenant isolation tests.

Verifies that data from one clinic is never accessible to users of another clinic,
and that clinic suspension immediately blocks in-flight sessions.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.enums import ClinicStatus, EmploymentType, UserRole, UserStatus
from app.models.user import User
from tests.conftest import login


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def clinic_b(db_session: Session) -> Clinic:
    """A second clinic with its own admin, isolated from the test clinic (A)."""
    b = Clinic(
        id=uuid4(),
        name="Beta Clinic",
        slug="beta-clinic",
        status=ClinicStatus.ACTIVE,
        timezone="Asia/Tokyo",
    )
    db_session.add(b)
    db_session.flush()

    db_session.add(User(
        id=uuid4(),
        clinic_id=b.id,
        name="Beta Admin",
        email="admin@beta.example",
        password_hash=hash_password("BetaAdminPass123"),
        role=UserRole.ADMIN,
        employment_type=EmploymentType.FULL_TIME,
        status=UserStatus.ACTIVE,
    ))
    db_session.commit()
    return b


# ---------------------------------------------------------------------------
# Same-email constraint
# ---------------------------------------------------------------------------

def test_same_email_two_clinics(db_session: Session, clinic_b: Clinic) -> None:
    """The same email address can exist in two different clinics without a constraint error."""
    # Clinic A already has admin@test.example — insert the same email into clinic B.
    user_b = User(
        id=uuid4(),
        clinic_id=clinic_b.id,
        name="Shared Email User",
        email="admin@test.example",
        password_hash=hash_password("SharedPass123"),
        role=UserRole.STAFF,
        employment_type=EmploymentType.FULL_TIME,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user_b)
    db_session.commit()  # Must not raise IntegrityError

    assert db_session.get(User, user_b.id) is not None


# ---------------------------------------------------------------------------
# Staff isolation
# ---------------------------------------------------------------------------

def test_staff_list_never_leaks_other_clinic(
    client: TestClient, db_session: Session, clinic_b: Clinic
) -> None:
    """GET /staff for a clinic A admin never includes clinic B records."""
    login(client, "admin@test.example", "AdminPass123")

    response = client.get("/staff")

    assert response.status_code == 200
    returned_clinic_ids = {member["clinic_id"] for member in response.json()}
    assert str(clinic_b.id) not in returned_clinic_ids


def test_cannot_access_other_clinic_staff_by_id(
    client: TestClient, db_session: Session, clinic_b: Clinic
) -> None:
    """A clinic A user gets 404 when fetching a clinic B user's ID directly."""
    staff_b = db_session.query(User).filter(User.clinic_id == clinic_b.id).first()
    assert staff_b is not None

    login(client, "admin@test.example", "AdminPass123")

    response = client.get(f"/staff/{staff_b.id}")

    assert response.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Leave type isolation
# ---------------------------------------------------------------------------

def test_leave_types_scoped_to_clinic(
    client: TestClient, db_session: Session, clinic_b: Clinic
) -> None:
    """A leave type created in clinic A is not visible to clinic B users."""
    login(client, "admin@test.example", "AdminPass123")
    create_resp = client.post(
        "/leave/types",
        json={"name": "Clinic A Secret Leave", "default_days_per_year": 3},
    )
    assert create_resp.status_code == 201
    leave_type_id = create_resp.json()["id"]

    login(client, "admin@beta.example", "BetaAdminPass123", clinic_slug="beta-clinic")
    list_resp = client.get("/leave/types")

    assert list_resp.status_code == 200
    returned_ids = [lt["id"] for lt in list_resp.json()]
    assert leave_type_id not in returned_ids


# ---------------------------------------------------------------------------
# Clinic profile isolation
# ---------------------------------------------------------------------------

def test_clinic_profile_scoped_to_own_clinic(
    client: TestClient, db_session: Session, clinic_b: Clinic
) -> None:
    """GET /clinics/me always returns the authenticated user's own clinic."""
    login(client, "admin@test.example", "AdminPass123")
    resp_a = client.get("/clinics/me")
    assert resp_a.status_code == 200
    assert resp_a.json()["id"] != str(clinic_b.id)
    assert resp_a.json()["slug"] == "test-clinic"

    login(client, "admin@beta.example", "BetaAdminPass123", clinic_slug="beta-clinic")
    resp_b = client.get("/clinics/me")
    assert resp_b.status_code == 200
    assert resp_b.json()["id"] == str(clinic_b.id)
    assert resp_b.json()["slug"] == "beta-clinic"


# ---------------------------------------------------------------------------
# Clinic suspension
# ---------------------------------------------------------------------------

def test_suspended_clinic_blocks_all_requests(
    client: TestClient, db_session: Session
) -> None:
    """Suspending a clinic immediately rejects authenticated requests — not only new logins."""
    login(client, "admin@test.example", "AdminPass123")
    assert client.get("/auth/me").status_code == 200

    # Suspend clinic A directly (no platform-admin API until MT-6).
    admin = db_session.query(User).filter(User.email == "admin@test.example").one()
    clinic_a = db_session.get(Clinic, admin.clinic_id)
    assert clinic_a is not None
    clinic_a.status = ClinicStatus.SUSPENDED
    db_session.commit()

    # The existing session cookie must now be rejected on every protected endpoint.
    assert client.get("/auth/me").status_code == 401
    assert client.get("/staff").status_code == 401


def test_active_clinic_not_affected_by_sibling_suspension(
    client: TestClient, db_session: Session, clinic_b: Clinic
) -> None:
    """Suspending clinic B does not affect clinic A users."""
    login(client, "admin@test.example", "AdminPass123")
    assert client.get("/auth/me").status_code == 200

    clinic_b.status = ClinicStatus.SUSPENDED
    db_session.commit()

    # Clinic A users are unaffected.
    assert client.get("/auth/me").status_code == 200
