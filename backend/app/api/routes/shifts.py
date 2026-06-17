from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.shift import ShiftCreateRequest, ShiftResponse, ShiftUpdateRequest
from app.services import shift_service

router = APIRouter(prefix="/shifts", tags=["shifts"])


def _handle(exc: shift_service.ShiftError) -> HTTPException:
    msg = str(exc)
    if msg == "Shift not found":
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    if msg == "Insufficient permissions":
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@router.get("", response_model=list[ShiftResponse])
def list_shifts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ShiftResponse]:
    shifts = shift_service.list_shifts(db, current_user)
    return [ShiftResponse.model_validate(s) for s in shifts]


@router.post("", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
def create_shift(
    payload: ShiftCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ShiftResponse:
    try:
        shift = shift_service.create_shift(db, current_user, payload)
    except shift_service.ShiftError as exc:
        raise _handle(exc) from exc
    return ShiftResponse.model_validate(shift)


@router.get("/{shift_id}", response_model=ShiftResponse)
def get_shift(
    shift_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ShiftResponse:
    try:
        shift = shift_service.get_shift(db, current_user, shift_id)
    except shift_service.ShiftError as exc:
        raise _handle(exc) from exc
    return ShiftResponse.model_validate(shift)


@router.patch("/{shift_id}", response_model=ShiftResponse)
def update_shift(
    shift_id: UUID,
    payload: ShiftUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ShiftResponse:
    try:
        shift = shift_service.update_shift(db, current_user, shift_id, payload)
    except shift_service.ShiftError as exc:
        raise _handle(exc) from exc
    return ShiftResponse.model_validate(shift)


@router.delete("/{shift_id}", response_model=ShiftResponse)
def deactivate_shift(
    shift_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ShiftResponse:
    try:
        shift = shift_service.deactivate_shift(db, current_user, shift_id)
    except shift_service.ShiftError as exc:
        raise _handle(exc) from exc
    return ShiftResponse.model_validate(shift)
