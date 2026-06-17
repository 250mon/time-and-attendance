from datetime import date
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import AuditAction
from app.models.user import User
from app.schemas.report import AttendanceSummaryRow, LeaveSummaryRow, MonthlyDetailRow
from app.services import audit_service, report_service as svc

router = APIRouter(prefix="/reports", tags=["reports"])

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ── Attendance Summary ────────────────────────────────────────────────────────

@router.get("/attendance-summary", response_model=None)
def attendance_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
    user_id: Annotated[str | None, Query()] = None,
    format: Annotated[str, Query()] = "json",
) -> Response | list[Any]:
    uid = UUID(user_id) if user_id else None
    rows = svc.attendance_summary(db, current_user, start_date, end_date, uid)

    if format == "xlsx":
        data = svc.attendance_summary_xlsx(rows, start_date, end_date)
        filename = f"attendance_summary_{start_date}_{end_date}.xlsx"
        audit_service.log_action(
            db, current_user.id, current_user.clinic_id, AuditAction.REPORT_EXPORTED,
            entity_type="report",
            metadata={"report_type": "attendance-summary", "start_date": str(start_date), "end_date": str(end_date)},
        )
        db.commit()
        return Response(
            content=data,
            media_type=XLSX_CONTENT_TYPE,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return [r.model_dump() for r in rows]


# ── Leave Summary ─────────────────────────────────────────────────────────────

@router.get("/leave-summary", response_model=None)
def leave_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: Annotated[int, Query()],
    user_id: Annotated[str | None, Query()] = None,
    format: Annotated[str, Query()] = "json",
) -> Response | list[Any]:
    uid = UUID(user_id) if user_id else None
    rows = svc.leave_summary(db, current_user, year, uid)

    if format == "xlsx":
        data = svc.leave_summary_xlsx(rows, year)
        audit_service.log_action(
            db, current_user.id, current_user.clinic_id, AuditAction.REPORT_EXPORTED,
            entity_type="report",
            metadata={"report_type": "leave-summary", "year": year},
        )
        db.commit()
        return Response(
            content=data,
            media_type=XLSX_CONTENT_TYPE,
            headers={"Content-Disposition": f'attachment; filename="leave_summary_{year}.xlsx"'},
        )
    return [r.model_dump() for r in rows]


# ── Monthly Detail ────────────────────────────────────────────────────────────

@router.get("/monthly-detail", response_model=None)
def monthly_detail(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: Annotated[int, Query()],
    month: Annotated[int, Query(ge=1, le=12)],
    user_id: Annotated[str | None, Query()] = None,
    format: Annotated[str, Query()] = "json",
) -> Response | list[Any]:
    uid = UUID(user_id) if user_id else None
    rows = svc.monthly_detail(db, current_user, year, month, uid)

    if format == "xlsx":
        data = svc.monthly_detail_xlsx(rows, year, month)
        audit_service.log_action(
            db, current_user.id, current_user.clinic_id, AuditAction.REPORT_EXPORTED,
            entity_type="report",
            metadata={"report_type": "monthly-detail", "year": year, "month": month},
        )
        db.commit()
        return Response(
            content=data,
            media_type=XLSX_CONTENT_TYPE,
            headers={"Content-Disposition": f'attachment; filename="monthly_detail_{year}_{month:02d}.xlsx"'},
        )
    return [r.model_dump() for r in rows]
