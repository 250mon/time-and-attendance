from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import can_manage_schedules
from app.db.session import get_db
from app.models.user import User
from app.schemas.attendance import AttendanceDayResponse, PunchResponse, TodayStatusResponse, UserDayPunches
from app.services import attendance_calculation_service, attendance_service

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _handle(exc: attendance_service.AttendanceError) -> HTTPException:
    msg = str(exc)
    if msg == "Insufficient permissions":
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@router.post("/clock-in", response_model=PunchResponse, status_code=status.HTTP_201_CREATED)
def clock_in(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PunchResponse:
    ip = request.client.host if request.client else None
    try:
        punch = attendance_service.clock_in(db, current_user, ip_address=ip)
    except attendance_service.AttendanceError as exc:
        raise _handle(exc) from exc
    return PunchResponse.model_validate(punch)


@router.post("/clock-out", response_model=PunchResponse, status_code=status.HTTP_201_CREATED)
def clock_out(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PunchResponse:
    ip = request.client.host if request.client else None
    try:
        punch = attendance_service.clock_out(db, current_user, ip_address=ip)
    except attendance_service.AttendanceError as exc:
        raise _handle(exc) from exc
    return PunchResponse.model_validate(punch)


@router.get("/today", response_model=TodayStatusResponse)
def get_today(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TodayStatusResponse:
    data = attendance_service.get_today_status(db, current_user)
    return TodayStatusResponse.model_validate(data)


@router.get("/me", response_model=list[PunchResponse])
def get_my_punches(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> list[PunchResponse]:
    punches = attendance_service.get_my_punches(db, current_user, days=days)
    return [PunchResponse.model_validate(p) for p in punches]


@router.get("/daily", response_model=list[UserDayPunches])
def get_daily(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    date: Annotated[date, Query()] = None,  # type: ignore[assignment]
) -> list[UserDayPunches]:
    from datetime import UTC, datetime as dt

    for_date = date if date is not None else dt.now(UTC).date()
    try:
        groups = attendance_service.get_daily_punches(db, current_user, for_date)
    except attendance_service.AttendanceError as exc:
        raise _handle(exc) from exc
    return [
        UserDayPunches(
            user_id=g["user_id"],
            user_name=g["user_name"],
            punches=[PunchResponse.model_validate(p) for p in g["punches"]],
            is_clocked_in=g["is_clocked_in"],
        )
        for g in groups
    ]


@router.get("/days", response_model=list[AttendanceDayResponse])
def get_attendance_days(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Annotated[date, Query()] = None,  # type: ignore[assignment]
    end_date: Annotated[date, Query()] = None,  # type: ignore[assignment]
    user_id: Annotated[str, Query()] = None,  # type: ignore[assignment]
) -> list[AttendanceDayResponse]:
    from datetime import UTC, datetime as dt, timedelta

    today = dt.now(UTC).date()
    sd = start_date if start_date is not None else (today - timedelta(days=29))
    ed = end_date if end_date is not None else today

    filter_uid = None
    if user_id is not None:
        if not can_manage_schedules(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        import uuid as _uuid
        filter_uid = _uuid.UUID(user_id)

    days = attendance_calculation_service.get_attendance_days(
        db,
        clinic_id=current_user.clinic_id,
        user_id=current_user.id,
        start_date=sd,
        end_date=ed,
        filter_user_id=filter_uid,
    )
    return [AttendanceDayResponse.model_validate(d) for d in days]


@router.get("/monthly", response_model=list[PunchResponse])
def get_monthly(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    month: Annotated[str, Query(pattern=r"^\d{4}-\d{2}$")] = None,  # type: ignore[assignment]
) -> list[PunchResponse]:
    from datetime import UTC, datetime as dt

    if month is None:
        now = dt.now(UTC)
        year, mon = now.year, now.month
    else:
        year, mon = int(month[:4]), int(month[5:])
    try:
        punches = attendance_service.get_monthly_punches(db, current_user, year, mon)
    except attendance_service.AttendanceError as exc:
        raise _handle(exc) from exc
    return [PunchResponse.model_validate(p) for p in punches]
