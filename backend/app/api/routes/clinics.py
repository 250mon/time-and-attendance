from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.clinic import Clinic
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.clinic import (
    ClinicCreateRequest,
    ClinicPublicResponse,
    ClinicResponse,
    ClinicUpdateRequest,
)
from app.services import clinic_service

router = APIRouter(prefix="/clinics", tags=["clinics"])


@router.post("", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED)
def create_clinic(
    payload: ClinicCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    x_bootstrap_secret: Annotated[str | None, Header()] = None,
) -> ClinicResponse:
    """Operator-only endpoint for provisioning a new clinic.
    Set CLINIC_BOOTSTRAP_SECRET in the environment to enable it.
    Pass the secret in the X-Bootstrap-Secret request header."""
    if not settings.clinic_bootstrap_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clinic onboarding is not enabled on this server",
        )
    if x_bootstrap_secret != settings.clinic_bootstrap_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bootstrap secret",
        )
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
    return ClinicResponse.model_validate(clinic)


@router.get("/by-slug/{slug}", response_model=ClinicPublicResponse)
def get_clinic_by_slug(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
) -> ClinicPublicResponse:
    """Public endpoint — used by the login form to confirm a clinic slug is valid.
    Returns only name and slug; never exposes id, address, or timezone."""
    clinic = db.query(Clinic).filter(Clinic.slug == slug.lower()).one_or_none()
    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")
    return ClinicPublicResponse.model_validate(clinic)


@router.get("/me", response_model=ClinicResponse)
def get_clinic_profile(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ClinicResponse:
    try:
        clinic = clinic_service.get_clinic(db, current_user)
    except clinic_service.ClinicError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ClinicResponse.model_validate(clinic)


@router.patch("/me", response_model=ClinicResponse)
def update_clinic_profile(
    payload: ClinicUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))],
) -> ClinicResponse:
    try:
        clinic = clinic_service.update_clinic(db, current_user, payload)
    except clinic_service.ClinicError as exc:
        message = str(exc)
        if "Invalid timezone" in message:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message
            ) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc
    return ClinicResponse.model_validate(clinic)
