from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.closing import MonthlyClosingResponse
from app.services import closing_service as svc

router = APIRouter(prefix="/closings", tags=["closings"])


def _handle(exc: svc.ClosingError) -> HTTPException:
    msg = str(exc)
    if "Only owners" in msg or "Insufficient" in msg:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    if "not locked" in msg.lower() or "already locked" in msg.lower():
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@router.get("", response_model=list[MonthlyClosingResponse])
def list_closings(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: Annotated[int | None, Query()] = None,
) -> list[MonthlyClosingResponse]:
    closings = svc.list_closings(db, current_user.clinic_id, year=year)
    return [MonthlyClosingResponse.model_validate(c) for c in closings]


@router.post("/{year}/{month}/lock", response_model=MonthlyClosingResponse)
def lock_month(
    year: int,
    month: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MonthlyClosingResponse:
    try:
        closing = svc.lock_month(db, current_user, year, month)
    except svc.ClosingError as exc:
        raise _handle(exc) from exc
    return MonthlyClosingResponse.model_validate(closing)


@router.post("/{year}/{month}/unlock", response_model=MonthlyClosingResponse)
def unlock_month(
    year: int,
    month: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MonthlyClosingResponse:
    try:
        closing = svc.unlock_month(db, current_user, year, month)
    except svc.ClosingError as exc:
        raise _handle(exc) from exc
    return MonthlyClosingResponse.model_validate(closing)
