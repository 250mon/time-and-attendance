from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import CorrectionStatus
from app.models.user import User
from app.schemas.correction import CorrectionCreateRequest, CorrectionResponse, ReviewRequest
from app.services import attendance_correction_service as svc

router = APIRouter(prefix="/attendance/corrections", tags=["corrections"])


def _handle(exc: svc.CorrectionError) -> HTTPException:
    msg = str(exc)
    if "Insufficient permissions" in msg or "Not found" in msg:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    if "not found" in msg.lower():
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@router.post("", response_model=CorrectionResponse, status_code=status.HTTP_201_CREATED)
def create_correction(
    payload: CorrectionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CorrectionResponse:
    try:
        req = svc.create_correction(
            db,
            current_user,
            work_date=payload.work_date,
            reason=payload.reason,
            corrected_clock_in=payload.corrected_clock_in,
            corrected_clock_out=payload.corrected_clock_out,
        )
    except svc.CorrectionError as exc:
        raise _handle(exc) from exc
    return CorrectionResponse.model_validate(req)


@router.get("", response_model=list[CorrectionResponse])
def list_corrections(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: Annotated[CorrectionStatus | None, Query(alias="status")] = None,
    user_id: Annotated[str | None, Query()] = None,
) -> list[CorrectionResponse]:
    uid_filter = UUID(user_id) if user_id else None
    reqs = svc.list_corrections(db, current_user, status_filter=status_filter, user_id_filter=uid_filter)
    return [CorrectionResponse.model_validate(r) for r in reqs]


@router.get("/{correction_id}", response_model=CorrectionResponse)
def get_correction(
    correction_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CorrectionResponse:
    try:
        req = svc.get_correction(db, current_user, correction_id)
    except svc.CorrectionError as exc:
        raise _handle(exc) from exc
    return CorrectionResponse.model_validate(req)


@router.post("/{correction_id}/approve", response_model=CorrectionResponse)
def approve_correction(
    correction_id: UUID,
    payload: ReviewRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CorrectionResponse:
    try:
        req = svc.approve_correction(db, current_user, correction_id, reviewer_note=payload.reviewer_note)
    except svc.CorrectionError as exc:
        raise _handle(exc) from exc
    return CorrectionResponse.model_validate(req)


@router.post("/{correction_id}/reject", response_model=CorrectionResponse)
def reject_correction(
    correction_id: UUID,
    payload: ReviewRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CorrectionResponse:
    try:
        req = svc.reject_correction(db, current_user, correction_id, reviewer_note=payload.reviewer_note)
    except svc.CorrectionError as exc:
        raise _handle(exc) from exc
    return CorrectionResponse.model_validate(req)


@router.delete("/{correction_id}", response_model=CorrectionResponse)
def cancel_correction(
    correction_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CorrectionResponse:
    try:
        req = svc.cancel_correction(db, current_user, correction_id)
    except svc.CorrectionError as exc:
        raise _handle(exc) from exc
    return CorrectionResponse.model_validate(req)
