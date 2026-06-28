import uuid
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import get_db
from app.models.clinic import Clinic
from app.models.enums import ClinicStatus, UserRole
from app.models.user import User
from app.schemas.clinic import ClinicCreateRequest
from app.schemas.platform import PlatformClinicResponse, PlatformClinicUpdateRequest, PlatformMetricsResponse
from app.services import clinic_service

router = APIRouter(prefix="/platform", tags=["platform"])


def _require_platform_token(
    x_platform_token: Annotated[str | None, Header()] = None,
) -> None:
    if not settings.platform_admin_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Platform admin is not enabled on this server",
        )
    if x_platform_token != settings.platform_admin_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid platform token",
        )


def _build_clinic_response(db: Session, clinic: Clinic) -> PlatformClinicResponse:
    count: int = (
        db.query(func.count(User.id)).filter(User.clinic_id == clinic.id).scalar() or 0
    )
    return PlatformClinicResponse(
        id=clinic.id,
        name=clinic.name,
        slug=clinic.slug,
        status=clinic.status,
        timezone=clinic.timezone,
        address=clinic.address,
        user_count=count,
        created_at=clinic.created_at,
        updated_at=clinic.updated_at,
    )


@router.get("/clinics", response_model=list[PlatformClinicResponse])
def list_platform_clinics(
    db: Annotated[Session, Depends(get_db)],
    _auth: Annotated[None, Depends(_require_platform_token)],
) -> list[PlatformClinicResponse]:
    rows = (
        db.query(Clinic, func.count(User.id).label("user_count"))
        .outerjoin(User, User.clinic_id == Clinic.id)
        .group_by(Clinic.id)
        .order_by(Clinic.created_at)
        .all()
    )
    return [
        PlatformClinicResponse(
            id=clinic.id,
            name=clinic.name,
            slug=clinic.slug,
            status=clinic.status,
            timezone=clinic.timezone,
            address=clinic.address,
            user_count=count,
            created_at=clinic.created_at,
            updated_at=clinic.updated_at,
        )
        for clinic, count in rows
    ]


@router.post("/clinics", response_model=PlatformClinicResponse, status_code=status.HTTP_201_CREATED)
def create_platform_clinic(
    payload: ClinicCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    _auth: Annotated[None, Depends(_require_platform_token)],
) -> PlatformClinicResponse:
    """Create a new clinic + owner account + default leave types via platform token."""
    try:
        clinic = clinic_service.create_clinic(db, payload)
    except clinic_service.ClinicError as exc:
        message = str(exc)
        if "Invalid timezone" in message:
            code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif "already in use" in message:
            code = status.HTTP_409_CONFLICT
        else:
            code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=message) from exc
    return _build_clinic_response(db, clinic)


@router.patch("/clinics/{clinic_id}", response_model=PlatformClinicResponse)
def update_platform_clinic(
    clinic_id: uuid.UUID,
    payload: PlatformClinicUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    _auth: Annotated[None, Depends(_require_platform_token)],
) -> PlatformClinicResponse:
    """Update clinic profile and/or owner credentials via platform token."""
    clinic = db.get(Clinic, clinic_id)
    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

    if payload.name is not None:
        clinic.name = payload.name.strip()

    if payload.timezone is not None:
        try:
            ZoneInfo(payload.timezone)
        except ZoneInfoNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid timezone: {payload.timezone!r}",
            )
        clinic.timezone = payload.timezone

    if payload.address is not None:
        clinic.address = payload.address.strip() or None

    if any(v is not None for v in [payload.owner_name, payload.owner_email, payload.owner_password]):
        owner = (
            db.query(User)
            .filter(User.clinic_id == clinic.id, User.role == UserRole.OWNER)
            .order_by(User.created_at)
            .first()
        )
        if owner is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No owner account found for this clinic",
            )
        if payload.owner_name is not None:
            owner.name = payload.owner_name.strip()
        if payload.owner_email is not None:
            new_email = str(payload.owner_email).lower()
            if new_email != owner.email:
                conflict = (
                    db.query(User)
                    .filter(
                        User.clinic_id == clinic.id,
                        User.email == new_email,
                        User.id != owner.id,
                    )
                    .first()
                )
                if conflict is not None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Email '{new_email}' is already in use in this clinic",
                    )
                owner.email = new_email
        if payload.owner_password is not None:
            owner.password_hash = hash_password(payload.owner_password)
        db.add(owner)

    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    return _build_clinic_response(db, clinic)


@router.get("/metrics", response_model=PlatformMetricsResponse)
def get_platform_metrics(
    db: Annotated[Session, Depends(get_db)],
    _auth: Annotated[None, Depends(_require_platform_token)],
) -> PlatformMetricsResponse:
    total_clinics: int = db.query(func.count(Clinic.id)).scalar() or 0
    active_clinics: int = (
        db.query(func.count(Clinic.id))
        .filter(Clinic.status == ClinicStatus.ACTIVE)
        .scalar()
        or 0
    )
    total_users: int = db.query(func.count(User.id)).scalar() or 0
    return PlatformMetricsResponse(
        total_clinics=total_clinics,
        active_clinics=active_clinics,
        suspended_clinics=total_clinics - active_clinics,
        total_users=total_users,
    )


@router.post(
    "/clinics/{clinic_id}/suspend",
    response_model=PlatformClinicResponse,
)
def suspend_clinic(
    clinic_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _auth: Annotated[None, Depends(_require_platform_token)],
) -> PlatformClinicResponse:
    clinic = db.get(Clinic, clinic_id)
    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")
    if clinic.status == ClinicStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Clinic is already suspended"
        )
    clinic.status = ClinicStatus.SUSPENDED
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    return _build_clinic_response(db, clinic)


@router.post(
    "/clinics/{clinic_id}/activate",
    response_model=PlatformClinicResponse,
)
def activate_clinic(
    clinic_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _auth: Annotated[None, Depends(_require_platform_token)],
) -> PlatformClinicResponse:
    clinic = db.get(Clinic, clinic_id)
    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")
    if clinic.status == ClinicStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Clinic is already active"
        )
    clinic.status = ClinicStatus.ACTIVE
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    return _build_clinic_response(db, clinic)
