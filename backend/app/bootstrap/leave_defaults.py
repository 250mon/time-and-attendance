from uuid import UUID

from sqlalchemy.orm import Session

from app.models.leave_type import LeaveType

# Korean Labor Standards Act (근로기준법) and Equal Employment Opportunity Act (남녀고용평등법)
_KR_DEFAULT_LEAVE_TYPES: list[dict] = [
    # LSA Art. 60 — fiscal-year bulk grant; balance auto-calculated from hire_date
    {"name": "연차유급휴가 (Annual Leave)", "default_days_per_year": None, "requires_approval": True, "tenure_based": True},
    # Clinic sick leave — usage tracked; max per request configurable
    {"name": "병가 (Sick Leave)", "default_days_per_year": None, "requires_approval": True},
    # LSA Art. 73 — 1 unpaid day per month
    {"name": "생리휴가 (Menstrual Leave)", "default_days_per_year": 1, "requires_approval": True},
    # LSA Art. 74 — 90 days (120 for multiple births) before/after childbirth
    {"name": "출산전후휴가 (Maternity Leave)", "default_days_per_year": 90, "requires_approval": True},
    # LSA Art. 75 — 10 paid days when spouse gives birth
    {"name": "배우자 출산휴가 (Paternity Leave)", "default_days_per_year": 10, "requires_approval": True},
    # EEOA Art. 19 — up to 1 year per child under age 8
    {"name": "육아휴직 (Parental Leave)", "default_days_per_year": 365, "requires_approval": True},
    # EEOA Art. 22-2 — 10 days per year for family care emergencies
    {"name": "가족돌봄휴가 (Family Care Leave)", "default_days_per_year": 10, "requires_approval": True},
]


def seed_default_leave_types(db: Session, clinic_id: UUID) -> None:
    existing = db.query(LeaveType).filter(LeaveType.clinic_id == clinic_id).first()
    if existing is not None:
        return
    for spec in _KR_DEFAULT_LEAVE_TYPES:
        db.add(LeaveType(clinic_id=clinic_id, **spec))
    db.commit()
