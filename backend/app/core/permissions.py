from uuid import UUID

from app.models.enums import UserRole, UserStatus
from app.models.user import User


def is_admin_role(role: UserRole) -> bool:
    return role in {UserRole.OWNER, UserRole.ADMIN}


def is_manager_or_above(role: UserRole) -> bool:
    return role in {UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER}


def can_create_staff(user: User) -> bool:
    return is_manager_or_above(user.role)


def can_edit_staff(actor: User, target: User) -> bool:
    if actor.id == target.id:
        return True
    if is_admin_role(actor.role):
        return True
    return actor.role == UserRole.MANAGER and target.role == UserRole.STAFF


def can_deactivate_staff(user: User) -> bool:
    return is_admin_role(user.role)


def can_view_staff_list(user: User) -> bool:
    return is_manager_or_above(user.role)


def can_view_staff_profile(actor: User, target_id: UUID) -> bool:
    if actor.id == target_id:
        return True
    return can_view_staff_list(actor)


def can_manage_shifts(user: User) -> bool:
    return is_manager_or_above(user.role)


def can_manage_schedules(user: User) -> bool:
    return is_manager_or_above(user.role)


def is_active_user(user: User) -> bool:
    return user.status == UserStatus.ACTIVE
