from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.schedule import (
    ScheduleCreateRequest,
    ScheduleGenerateRequest,
    ScheduleResponse,
    ScheduleUpdateRequest,
)
from app.services import schedule_service

router = APIRouter(prefix="/schedules", tags=["schedules"])


def _handle(exc: schedule_service.ScheduleError) -> HTTPException:
    msg = str(exc)
    if msg == "Schedule not found":
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    if msg == "Insufficient permissions":
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@router.get("", response_model=list[ScheduleResponse])
def list_schedules(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    user_id: Annotated[UUID | None, Query()] = None,
) -> list[ScheduleResponse]:
    schedules = schedule_service.list_schedules(db, current_user, start_date, end_date, user_id)
    return [ScheduleResponse.model_validate(s) for s in schedules]


@router.post("/generate", response_model=list[ScheduleResponse], status_code=status.HTTP_201_CREATED)
def generate_schedules(
    payload: ScheduleGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ScheduleResponse]:
    try:
        schedules = schedule_service.generate_schedules(db, current_user, payload)
    except schedule_service.ScheduleError as exc:
        raise _handle(exc) from exc
    return [ScheduleResponse.model_validate(s) for s in schedules]


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ScheduleResponse:
    try:
        schedule = schedule_service.create_schedule(db, current_user, payload)
    except schedule_service.ScheduleError as exc:
        raise _handle(exc) from exc
    return ScheduleResponse.model_validate(schedule)


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: UUID,
    payload: ScheduleUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ScheduleResponse:
    try:
        schedule = schedule_service.update_schedule(db, current_user, schedule_id, payload)
    except schedule_service.ScheduleError as exc:
        raise _handle(exc) from exc
    return ScheduleResponse.model_validate(schedule)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    try:
        schedule_service.delete_schedule(db, current_user, schedule_id)
    except schedule_service.ScheduleError as exc:
        raise _handle(exc) from exc
