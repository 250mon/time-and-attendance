from datetime import date

from sqlalchemy.orm import Session

from app.bootstrap.leave_defaults import seed_default_leave_types
from app.core.config import settings
from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.enums import ClinicStatus, EmploymentType, UserRole, UserStatus
from app.models.user import User
from app.services.leave_balance_service import assign_default_balances

_SAMPLE_STAFF = [
    {
        "name": "Kim Minji",
        "email": "minji@clinic.example",
        "hire_date": date(2024, 6, 13),  # 15 days on 2026-01-01 (2nd fiscal grant)
    },
    {
        "name": "Lee Jaesung",
        "email": "jaesung@clinic.example",
        "hire_date": date(2025, 6, 13),  # 8.8 days on 2026-01-01 (proportional 1st grant)
    },
]


def seed_default_clinic_and_admin(db: Session) -> None:
    existing_user = db.query(User).first()
    if existing_user is not None:
        return

    clinic = Clinic(
        name=settings.seed_clinic_name,
        slug=settings.seed_clinic_slug,
        status=ClinicStatus.ACTIVE,
        timezone=settings.clinic_timezone,
    )
    db.add(clinic)
    db.flush()

    admin = User(
        clinic_id=clinic.id,
        name=settings.seed_admin_name,
        email=settings.seed_admin_email.lower(),
        password_hash=hash_password(settings.seed_admin_password),
        role=UserRole.OWNER,
        employment_type=EmploymentType.FULL_TIME,
        status=UserStatus.ACTIVE,
    )
    db.add(admin)
    db.commit()


def seed_sample_staff(db: Session) -> None:
    clinic = db.query(Clinic).first()
    if clinic is None:
        return
    for spec in _SAMPLE_STAFF:
        exists = (
            db.query(User)
            .filter(User.clinic_id == clinic.id, User.email == spec["email"])
            .first()
        )
        if exists:
            continue
        user = User(
            clinic_id=clinic.id,
            name=spec["name"],
            email=spec["email"],
            password_hash=hash_password("Sample123!"),
            role=UserRole.STAFF,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=spec["hire_date"],
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        assign_default_balances(db, user)


def run_startup_seed(db: Session) -> None:
    """Idempotent dev bootstrap: demo clinic, leave types, and sample staff."""
    seed_default_clinic_and_admin(db)
    clinic = db.query(Clinic).first()
    if clinic is not None:
        seed_default_leave_types(db, clinic.id)
    seed_sample_staff(db)
