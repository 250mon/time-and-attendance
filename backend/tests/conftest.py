import os
from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.clinic import Clinic
from app.models.enums import ClinicStatus, EmploymentType, UserRole, UserStatus
from app.models.user import User

_default_test_url = "postgresql+psycopg://clinic_time_user:change_me@localhost:5432/clinic_time_test"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", _default_test_url)


@pytest.fixture(scope="session")
def engine():
    test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=engine, checkfirst=True)
    Base.metadata.create_all(bind=engine)

    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    clinic = Clinic(
        id=uuid4(),
        name="Test Clinic",
        slug="test-clinic",
        status=ClinicStatus.ACTIVE,
        timezone="Asia/Seoul",
    )
    session.add(clinic)
    session.flush()

    admin = User(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Admin User",
        email="admin@test.example",
        password_hash=hash_password("AdminPass123"),
        role=UserRole.ADMIN,
        employment_type=EmploymentType.FULL_TIME,
        status=UserStatus.ACTIVE,
    )
    manager = User(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Manager User",
        email="manager@test.example",
        password_hash=hash_password("ManagerPass123"),
        role=UserRole.MANAGER,
        employment_type=EmploymentType.FULL_TIME,
        status=UserStatus.ACTIVE,
    )
    staff = User(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Staff User",
        email="staff@test.example",
        password_hash=hash_password("StaffPass123"),
        role=UserRole.STAFF,
        employment_type=EmploymentType.FULL_TIME,
        status=UserStatus.ACTIVE,
    )
    inactive = User(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Inactive User",
        email="inactive@test.example",
        password_hash=hash_password("InactivePass123"),
        role=UserRole.STAFF,
        employment_type=EmploymentType.FULL_TIME,
        status=UserStatus.INACTIVE,
    )
    session.add_all([admin, manager, staff, inactive])
    session.commit()

    yield session

    session.close()


@pytest.fixture(autouse=True)
def disable_startup_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.main.run_startup_seed", lambda _db: None)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def login(client: TestClient, email: str, password: str, clinic_slug: str | None = None) -> None:
    payload: dict = {"email": email, "password": password}
    if clinic_slug:
        payload["clinic_slug"] = clinic_slug
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200, response.text
