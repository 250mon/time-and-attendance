from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import UserStatus
from app.models.user import User
from tests.conftest import login


def test_staff_cannot_list_staff(client: TestClient) -> None:
    login(client, "staff@test.example", "StaffPass123")

    response = client.get("/staff")

    assert response.status_code == 403


def test_manager_can_list_staff(client: TestClient) -> None:
    login(client, "manager@test.example", "ManagerPass123")

    response = client.get("/staff")

    assert response.status_code == 200
    assert len(response.json()) >= 3


def test_admin_can_create_staff(client: TestClient) -> None:
    login(client, "admin@test.example", "AdminPass123")

    response = client.post(
        "/staff",
        json={
            "name": "New Nurse",
            "email": "nurse@test.example",
            "password": "NursePass123",
            "role": "STAFF",
            "employment_type": "FULL_TIME",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "nurse@test.example"


def test_staff_can_view_own_profile(client: TestClient, db_session: Session) -> None:
    login(client, "staff@test.example", "StaffPass123")
    staff = db_session.query(User).filter(User.email == "staff@test.example").one()

    response = client.get(f"/staff/{staff.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(staff.id)


def test_staff_cannot_view_other_staff_profile(client: TestClient, db_session: Session) -> None:
    login(client, "staff@test.example", "StaffPass123")
    admin = db_session.query(User).filter(User.email == "admin@test.example").one()

    response = client.get(f"/staff/{admin.id}")

    assert response.status_code == 403


def test_admin_can_deactivate_staff(client: TestClient, db_session: Session) -> None:
    login(client, "admin@test.example", "AdminPass123")
    staff = db_session.query(User).filter(User.email == "staff@test.example").one()

    response = client.delete(f"/staff/{staff.id}")

    assert response.status_code == 200
    assert response.json()["status"] == "INACTIVE"

    db_session.refresh(staff)
    assert staff.status == UserStatus.INACTIVE


def test_deactivation_preserves_user_row(client: TestClient, db_session: Session) -> None:
    login(client, "admin@test.example", "AdminPass123")
    staff = db_session.query(User).filter(User.email == "staff@test.example").one()
    staff_id = staff.id

    client.delete(f"/staff/{staff_id}")

    preserved = db_session.get(User, staff_id)
    assert preserved is not None
    assert preserved.status == UserStatus.INACTIVE


def test_manager_cannot_deactivate_staff(client: TestClient, db_session: Session) -> None:
    login(client, "manager@test.example", "ManagerPass123")
    staff = db_session.query(User).filter(User.email == "staff@test.example").one()

    response = client.delete(f"/staff/{staff.id}")

    assert response.status_code == 403


def test_admin_can_update_staff_name(client: TestClient, db_session: Session) -> None:
    login(client, "admin@test.example", "AdminPass123")
    staff = db_session.query(User).filter(User.email == "staff@test.example").one()

    response = client.patch(f"/staff/{staff.id}", json={"name": "Updated Name"})

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_staff_can_update_own_profile(client: TestClient, db_session: Session) -> None:
    login(client, "staff@test.example", "StaffPass123")
    staff = db_session.query(User).filter(User.email == "staff@test.example").one()

    response = client.patch(f"/staff/{staff.id}", json={"name": "Self Updated"})

    assert response.status_code == 200
    assert response.json()["name"] == "Self Updated"


def test_staff_cannot_update_other_profile(client: TestClient, db_session: Session) -> None:
    login(client, "staff@test.example", "StaffPass123")
    admin = db_session.query(User).filter(User.email == "admin@test.example").one()

    response = client.patch(f"/staff/{admin.id}", json={"name": "Hacked"})

    assert response.status_code == 403


def test_patch_can_clear_nullable_fields(client: TestClient, db_session: Session) -> None:
    login(client, "admin@test.example", "AdminPass123")
    staff = db_session.query(User).filter(User.email == "staff@test.example").one()

    client.patch(f"/staff/{staff.id}", json={"phone": "010-1234-5678", "hire_date": "2024-01-01"})

    clear_response = client.patch(
        f"/staff/{staff.id}", json={"phone": None, "hire_date": None}
    )

    assert clear_response.status_code == 200
    body = clear_response.json()
    assert body["phone"] is None
    assert body["hire_date"] is None


def test_non_owner_cannot_assign_admin_role(client: TestClient, db_session: Session) -> None:
    login(client, "admin@test.example", "AdminPass123")
    staff = db_session.query(User).filter(User.email == "staff@test.example").one()

    response = client.patch(f"/staff/{staff.id}", json={"role": "OWNER"})

    assert response.status_code == 400
