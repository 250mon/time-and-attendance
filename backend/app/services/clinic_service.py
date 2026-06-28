from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.bootstrap.leave_defaults import seed_default_leave_types
from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.enums import ClinicStatus, EmploymentType, UserRole, UserStatus
from app.models.user import User
from app.schemas.clinic import ClinicCreateRequest, ClinicUpdateRequest


class ClinicError(Exception):
    pass


def create_clinic(db: Session, payload: ClinicCreateRequest) -> Clinic:
    """Bootstrap a new clinic with an owner account and default leave types.

    Callers must verify CLINIC_BOOTSTRAP_SECRET before calling this function.
    """
    existing_slug = db.query(Clinic).filter(Clinic.slug == payload.slug).one_or_none()
    if existing_slug is not None:
        raise ClinicError(f"Slug '{payload.slug}' is already in use")

    try:
        ZoneInfo(payload.timezone)
    except ZoneInfoNotFoundError as exc:
        raise ClinicError(f"Invalid timezone: {payload.timezone!r}") from exc

    clinic = Clinic(
        name=payload.name.strip(),
        slug=payload.slug,
        status=ClinicStatus.ACTIVE,
        timezone=payload.timezone,
        address=payload.address.strip() if payload.address else None,
    )
    db.add(clinic)
    db.flush()

    owner = User(
        clinic_id=clinic.id,
        name=payload.owner_name.strip(),
        email=str(payload.owner_email).lower(),
        password_hash=hash_password(payload.owner_password),
        role=UserRole.OWNER,
        employment_type=EmploymentType.FULL_TIME,
        status=UserStatus.ACTIVE,
    )
    db.add(owner)
    db.flush()

    seed_default_leave_types(db, clinic.id)
    db.refresh(clinic)
    return clinic


def get_clinic(db: Session, actor: User) -> Clinic:
    clinic = db.get(Clinic, actor.clinic_id)
    if clinic is None:
        raise ClinicError("Clinic not found")
    return clinic


def update_clinic(db: Session, actor: User, payload: ClinicUpdateRequest) -> Clinic:
    if actor.role not in {UserRole.OWNER, UserRole.ADMIN}:
        raise ClinicError("Insufficient permissions")

    clinic = db.get(Clinic, actor.clinic_id)
    if clinic is None:
        raise ClinicError("Clinic not found")

    if payload.name is not None:
        clinic.name = payload.name.strip()

    if payload.timezone is not None:
        try:
            ZoneInfo(payload.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ClinicError(f"Invalid timezone: {payload.timezone!r}") from exc
        clinic.timezone = payload.timezone

    if payload.address is not None:
        clinic.address = payload.address.strip() or None

    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    return clinic
