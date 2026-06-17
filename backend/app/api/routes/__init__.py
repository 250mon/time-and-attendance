from fastapi import APIRouter

from app.api.routes import attendance, audit_logs, auth, closings, corrections, health, leave, reports, schedules, shifts, staff

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(staff.router)
api_router.include_router(shifts.router)
api_router.include_router(schedules.router)
api_router.include_router(attendance.router)
api_router.include_router(corrections.router)
api_router.include_router(leave.router)
api_router.include_router(reports.router)
api_router.include_router(closings.router)
api_router.include_router(audit_logs.router)
