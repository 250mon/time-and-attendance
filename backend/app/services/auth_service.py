from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.clinic import Clinic
from app.models.enums import ClinicStatus, UserStatus
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest


class AuthError(Exception):
    pass


def authenticate_user(db: Session, payload: LoginRequest) -> User:
    if payload.clinic_slug:
        clinic = (
            db.query(Clinic)
            .filter(Clinic.slug == payload.clinic_slug.lower())
            .one_or_none()
        )
        if clinic is None or clinic.status != ClinicStatus.ACTIVE:
            raise AuthError("Invalid email or password")
    elif not settings.multi_tenant_enabled:
        clinic = db.query(Clinic).first()
        if clinic is None:
            raise AuthError("Invalid email or password")
    else:
        raise AuthError("Clinic ID is required")

    user = (
        db.query(User)
        .filter(User.clinic_id == clinic.id, User.email == payload.email.lower())
        .one_or_none()
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AuthError("Invalid email or password")
    if user.status != UserStatus.ACTIVE:
        raise AuthError("Account is inactive")
    return user


def issue_access_token(user: User) -> str:
    return create_access_token(user.id, user.clinic_id)


def get_current_user_profile(user: User) -> User:
    return user


def change_password(db: Session, user: User, payload: ChangePasswordRequest) -> None:
    if not verify_password(payload.current_password, user.password_hash):
        raise AuthError("Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()
