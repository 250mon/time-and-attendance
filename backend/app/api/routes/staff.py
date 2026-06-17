from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import StaffCreateRequest, StaffUpdateRequest, UserResponse
from app.services import staff_service

router = APIRouter(prefix="/staff", tags=["staff"])


def _handle_staff_error(exc: staff_service.StaffError) -> HTTPException:
    message = str(exc)
    if message == "Staff member not found":
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    if message == "Insufficient permissions":
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("", response_model=list[UserResponse])
def list_staff(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[UserResponse]:
    try:
        staff = staff_service.list_staff(db, current_user)
    except staff_service.StaffError as exc:
        raise _handle_staff_error(exc) from exc
    return [UserResponse.model_validate(member) for member in staff]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: StaffCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    try:
        user = staff_service.create_staff_member(db, current_user, payload)
    except staff_service.StaffError as exc:
        raise _handle_staff_error(exc) from exc
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_staff(
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    try:
        user = staff_service.get_staff_member(db, current_user, user_id)
    except staff_service.StaffError as exc:
        raise _handle_staff_error(exc) from exc
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_staff(
    user_id: UUID,
    payload: StaffUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    try:
        user = staff_service.update_staff_member(db, current_user, user_id, payload)
    except staff_service.StaffError as exc:
        raise _handle_staff_error(exc) from exc
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", response_model=UserResponse)
def deactivate_staff(
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    try:
        user = staff_service.deactivate_staff_member(db, current_user, user_id)
    except staff_service.StaffError as exc:
        raise _handle_staff_error(exc) from exc
    return UserResponse.model_validate(user)
