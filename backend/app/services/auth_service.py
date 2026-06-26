from datetime import date

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.clinic import Clinic
from app.models.enums import EmploymentType, UserRole, UserStatus
from app.models.leave_type import LeaveType
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest
from app.services.leave_balance_service import assign_default_balances


class AuthError(Exception):
    pass


def authenticate_user(db: Session, payload: LoginRequest) -> User:
    user = db.query(User).filter(User.email == payload.email.lower()).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AuthError("Invalid email or password")
    if user.status != UserStatus.ACTIVE:
        raise AuthError("Account is inactive")
    return user


def issue_access_token(user: User) -> str:
    return create_access_token(user.id)


def get_current_user_profile(user: User) -> User:
    return user


def change_password(db: Session, user: User, payload: ChangePasswordRequest) -> None:
    if not verify_password(payload.current_password, user.password_hash):
        raise AuthError("Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()


def seed_default_clinic_and_admin(db: Session) -> None:
    existing_user = db.query(User).first()
    if existing_user is not None:
        return

    clinic = Clinic(
        name=settings.seed_clinic_name,
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


# Korean Labor Standards Act (근로기준법) and Equal Employment Opportunity Act (남녀고용평등법)
_KR_DEFAULT_LEAVE_TYPES: list[dict] = [
    # LSA Art. 60 — entitlement varies by tenure; balance is auto-calculated from hire_date
    {"name": "연차유급휴가 (Annual Leave)", "default_days_per_year": None, "requires_approval": True, "tenure_based": True},
    # LSA Art. 73 — 1 unpaid day per month; no manager approval required (statutory right)
    {"name": "생리휴가 (Menstrual Leave)", "default_days_per_year": 12, "requires_approval": False},
    # LSA Art. 74 — 90 days (120 for multiple births) before/after childbirth
    {"name": "출산전후휴가 (Maternity Leave)", "default_days_per_year": 90, "requires_approval": True},
    # LSA Art. 75 — 10 paid days when spouse gives birth
    {"name": "배우자 출산휴가 (Paternity Leave)", "default_days_per_year": 10, "requires_approval": True},
    # EEOA Art. 19 — up to 1 year per child under age 8
    {"name": "육아휴직 (Parental Leave)", "default_days_per_year": 365, "requires_approval": True},
    # EEOA Art. 22-2 — 10 days per year for family care emergencies
    {"name": "가족돌봄휴가 (Family Care Leave)", "default_days_per_year": 10, "requires_approval": True},
]


def seed_default_leave_types(db: Session) -> None:
    clinic = db.query(Clinic).first()
    if clinic is None:
        return
    existing = db.query(LeaveType).filter(LeaveType.clinic_id == clinic.id).first()
    if existing is not None:
        return
    for spec in _KR_DEFAULT_LEAVE_TYPES:
        db.add(LeaveType(clinic_id=clinic.id, **spec))
    db.commit()


_SAMPLE_STAFF = [
    {
        "name": "Kim Minji",
        "email": "minji@clinic.example",
        "hire_date": date(2024, 6, 13),  # 2 years of service as of 2026-06-13
    },
    {
        "name": "Lee Jaesung",
        "email": "jaesung@clinic.example",
        "hire_date": date(2025, 6, 13),  # 1 year of service as of 2026-06-13
    },
]


def seed_sample_staff(db: Session) -> None:
    clinic = db.query(Clinic).first()
    if clinic is None:
        return
    for spec in _SAMPLE_STAFF:
        exists = db.query(User).filter(User.email == spec["email"]).first()
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
