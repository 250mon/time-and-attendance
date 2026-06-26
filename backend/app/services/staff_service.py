from uuid import UUID

from sqlalchemy.orm import Session

from app.core.permissions import (
    can_create_staff,
    can_deactivate_staff,
    can_edit_staff,
    can_view_staff_list,
    can_view_staff_profile,
)
from app.core.security import hash_password
from app.models.enums import UserRole, UserStatus
from app.models.user import User
from app.schemas.user import StaffCreateRequest, StaffUpdateRequest
from app.services.leave_balance_service import assign_default_balances


class StaffError(Exception):
    pass


def list_staff(db: Session, actor: User) -> list[User]:
    if not can_view_staff_list(actor):
        raise StaffError("Insufficient permissions")

    return (
        db.query(User)
        .filter(User.clinic_id == actor.clinic_id)
        .order_by(User.name.asc())
        .all()
    )


def get_staff_member(db: Session, actor: User, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None or user.clinic_id != actor.clinic_id:
        raise StaffError("Staff member not found")
    if not can_view_staff_profile(actor, user.id):
        raise StaffError("Insufficient permissions")
    return user


def create_staff_member(db: Session, actor: User, payload: StaffCreateRequest) -> User:
    if not can_create_staff(actor):
        raise StaffError("Insufficient permissions")

    if payload.role in {UserRole.OWNER, UserRole.ADMIN} and actor.role != UserRole.OWNER:
        raise StaffError("Only owners can assign owner or admin roles")

    existing = db.query(User).filter(User.email == payload.email.lower()).one_or_none()
    if existing is not None:
        raise StaffError("Email is already in use")

    user = User(
        clinic_id=actor.clinic_id,
        name=payload.name.strip(),
        email=payload.email.lower(),
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=payload.role,
        employment_type=payload.employment_type,
        hire_date=payload.hire_date,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    assign_default_balances(db, user)
    return user


def update_staff_member(
    db: Session,
    actor: User,
    user_id: UUID,
    payload: StaffUpdateRequest,
) -> User:
    user = get_staff_member(db, actor, user_id)
    if not can_edit_staff(actor, user):
        raise StaffError("Insufficient permissions")

    updates = payload.model_dump(exclude_unset=True)

    if "role" in updates and updates["role"] in {UserRole.OWNER, UserRole.ADMIN}:
        if actor.role != UserRole.OWNER:
            raise StaffError("Only owners can assign owner or admin roles")

    if "status" in updates:
        if updates["status"] != UserStatus.ACTIVE and not can_deactivate_staff(actor):
            raise StaffError("Insufficient permissions")

    if "email" in updates and updates["email"] is not None:
        normalized = updates["email"].lower()
        existing = (
            db.query(User)
            .filter(User.email == normalized, User.id != user.id)
            .one_or_none()
        )
        if existing is not None:
            raise StaffError("Email is already in use")
        updates["email"] = normalized

    if "name" in updates and updates["name"] is not None:
        updates["name"] = updates["name"].strip()

    for field, value in updates.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def deactivate_staff_member(db: Session, actor: User, user_id: UUID) -> User:
    if not can_deactivate_staff(actor):
        raise StaffError("Insufficient permissions")

    user = get_staff_member(db, actor, user_id)
    if user.id == actor.id:
        raise StaffError("You cannot deactivate your own account")

    user.status = UserStatus.INACTIVE
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
