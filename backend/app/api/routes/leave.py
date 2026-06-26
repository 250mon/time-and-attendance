from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import LeaveStatus
from app.models.user import User
from app.schemas.leave import (
    LeaveRequestCreateRequest,
    LeaveRequestResponse,
    LeaveTypeCreateRequest,
    LeaveTypeResponse,
    LeaveTypeUpdateRequest,
    ReviewLeaveRequest,
)
from app.schemas.leave_balance import AdjustBalanceRequest, LeaveBalanceResponse
from app.services import leave_balance_service as balance_svc
from app.services import leave_request_service as req_svc
from app.services import leave_type_service as type_svc

router = APIRouter(prefix="/leave", tags=["leave"])


def _handle_type(exc: type_svc.LeaveTypeError) -> HTTPException:
    msg = str(exc)
    if "Insufficient" in msg or "not found" in msg.lower():
        code = status.HTTP_403_FORBIDDEN if "Insufficient" in msg else status.HTTP_404_NOT_FOUND
        return HTTPException(status_code=code, detail=msg)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


def _handle_req(exc: req_svc.LeaveRequestError) -> HTTPException:
    msg = str(exc)
    if "Insufficient" in msg:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    if "not found" in msg.lower():
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


# ── Leave Types ──────────────────────────────────────────────────────────────

@router.get("/types", response_model=list[LeaveTypeResponse])
def list_leave_types(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    include_inactive: bool = False,
) -> list[LeaveTypeResponse]:
    types = type_svc.list_leave_types(db, current_user.clinic_id, include_inactive=include_inactive)
    return [LeaveTypeResponse.model_validate(t) for t in types]


@router.post("/types", response_model=LeaveTypeResponse, status_code=status.HTTP_201_CREATED)
def create_leave_type(
    payload: LeaveTypeCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeaveTypeResponse:
    try:
        lt = type_svc.create_leave_type(
            db, current_user,
            name=payload.name,
            default_days_per_year=payload.default_days_per_year,
            requires_approval=payload.requires_approval,
            tenure_based=payload.tenure_based,
        )
    except type_svc.LeaveTypeError as exc:
        raise _handle_type(exc) from exc
    return LeaveTypeResponse.model_validate(lt)


@router.patch("/types/{leave_type_id}", response_model=LeaveTypeResponse)
def update_leave_type(
    leave_type_id: UUID,
    payload: LeaveTypeUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeaveTypeResponse:
    updates = payload.model_dump(exclude_unset=True)
    try:
        lt = type_svc.update_leave_type(db, current_user, leave_type_id, **updates)
    except type_svc.LeaveTypeError as exc:
        raise _handle_type(exc) from exc
    return LeaveTypeResponse.model_validate(lt)


@router.delete("/types/{leave_type_id}", response_model=LeaveTypeResponse)
def deactivate_leave_type(
    leave_type_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeaveTypeResponse:
    try:
        lt = type_svc.deactivate_leave_type(db, current_user, leave_type_id)
    except type_svc.LeaveTypeError as exc:
        raise _handle_type(exc) from exc
    return LeaveTypeResponse.model_validate(lt)


# ── Leave Requests ────────────────────────────────────────────────────────────

@router.post("/requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def create_leave_request(
    payload: LeaveRequestCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeaveRequestResponse:
    try:
        req = req_svc.create_leave_request(
            db, current_user,
            leave_type_id=payload.leave_type_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            reason=payload.reason,
        )
    except req_svc.LeaveRequestError as exc:
        raise _handle_req(exc) from exc
    return req_svc.build_leave_request_response(db, req)


@router.get("/requests", response_model=list[LeaveRequestResponse])
def list_leave_requests(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: Annotated[LeaveStatus | None, Query(alias="status")] = None,
    user_id: Annotated[str | None, Query()] = None,
) -> list[LeaveRequestResponse]:
    uid = UUID(user_id) if user_id else None
    reqs = req_svc.list_leave_requests(db, current_user, status_filter=status_filter, user_id_filter=uid)
    return req_svc.build_leave_request_responses(db, reqs)


@router.get("/requests/{request_id}", response_model=LeaveRequestResponse)
def get_leave_request(
    request_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeaveRequestResponse:
    try:
        req = req_svc.get_leave_request(db, current_user, request_id)
    except req_svc.LeaveRequestError as exc:
        raise _handle_req(exc) from exc
    return req_svc.build_leave_request_response(db, req)


@router.post("/requests/{request_id}/approve", response_model=LeaveRequestResponse)
def approve_leave_request(
    request_id: UUID,
    payload: ReviewLeaveRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeaveRequestResponse:
    try:
        req = req_svc.approve_leave_request(db, current_user, request_id, reviewer_note=payload.reviewer_note)
    except req_svc.LeaveRequestError as exc:
        raise _handle_req(exc) from exc
    return req_svc.build_leave_request_response(db, req)


@router.post("/requests/{request_id}/reject", response_model=LeaveRequestResponse)
def reject_leave_request(
    request_id: UUID,
    payload: ReviewLeaveRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeaveRequestResponse:
    try:
        req = req_svc.reject_leave_request(db, current_user, request_id, reviewer_note=payload.reviewer_note)
    except req_svc.LeaveRequestError as exc:
        raise _handle_req(exc) from exc
    return req_svc.build_leave_request_response(db, req)


@router.delete("/requests/{request_id}", response_model=LeaveRequestResponse)
def cancel_leave_request(
    request_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeaveRequestResponse:
    try:
        req = req_svc.cancel_leave_request(db, current_user, request_id)
    except req_svc.LeaveRequestError as exc:
        raise _handle_req(exc) from exc
    return req_svc.build_leave_request_response(db, req)


# ── Leave Balances ────────────────────────────────────────────────────────────

def _handle_balance(exc: balance_svc.LeaveBalanceError) -> HTTPException:
    msg = str(exc)
    if "Insufficient" in msg:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    if "not found" in msg.lower():
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@router.get("/balances", response_model=list[LeaveBalanceResponse])
def list_leave_balances(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    user_id: Annotated[str | None, Query()] = None,
    year: Annotated[int | None, Query()] = None,
) -> list[LeaveBalanceResponse]:
    uid = UUID(user_id) if user_id else None
    balances = balance_svc.list_balances(db, current_user, user_id=uid, year=year)
    return [LeaveBalanceResponse.from_orm_with_remaining(b) for b in balances]


@router.post("/balances/adjust", response_model=LeaveBalanceResponse)
def adjust_leave_balance(
    payload: AdjustBalanceRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> LeaveBalanceResponse:
    try:
        balance = balance_svc.adjust_balance(
            db, current_user,
            user_id=payload.user_id,
            leave_type_id=payload.leave_type_id,
            year=payload.year,
            delta_days=payload.delta_days,
            reason=payload.reason,
        )
    except balance_svc.LeaveBalanceError as exc:
        raise _handle_balance(exc) from exc
    return LeaveBalanceResponse.from_orm_with_remaining(balance)
