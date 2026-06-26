# Step-by-Step Development Guide

# Clinic Time & Attendance + Leave Management Software

## 1. Recommended MVP Stack

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS or MUI
- React Hook Form
- Zod for validation
- TanStack Query, optional

### Backend

- FastAPI
- Python 3.12+
- SQLAlchemy 2.x
- Alembic
- Pydantic
- PostgreSQL

### Infrastructure

- Docker Compose
- PostgreSQL
- Nginx reverse proxy, optional
- Daily database backup script
- GitHub Actions, optional

### Authentication

- Email/password login
- Secure HTTP-only cookie session or JWT access/refresh token
- Password hashing with Argon2id or bcrypt
- Role-based access control

### Initial Deployment Target

For a small clinic, start with:

```text
Next.js frontend
FastAPI backend
PostgreSQL database
Docker Compose deployment
```

------

# 2. Development Phases

Build the system in the following order:

```text
Phase 0: Project foundation
Phase 1: Authentication and staff management
Phase 2: Shift and schedule management
Phase 3: Clock-in / clock-out
Phase 4: Attendance calculation
Phase 5: Correction request workflow
Phase 6: Leave management
Phase 7: Leave balance engine
Phase 8: Reports and exports
Phase 9: Monthly closing and audit log
Phase 10: Testing, deployment, and hardening
```

Do not start with payroll integration, GPS, QR code, or biometric integration. Those should be post-MVP enhancements.

------

# 3. Phase 0 — Project Foundation

## 3.1 Create Repository Structure

Recommended monorepo:

```text
clinic-time/
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── Dockerfile
├── infra/
│   ├── nginx/
│   └── backup/
├── docker-compose.yml
├── .env.example
└── README.md
```

## 3.2 Create Docker Compose

Services:

```text
frontend
backend
postgres
```

Optional later:

```text
redis
nginx
worker
```

## 3.3 Environment Variables

Create `.env.example`:

```env
POSTGRES_DB=clinic_time
POSTGRES_USER=clinic_time_user
POSTGRES_PASSWORD=change_me
DATABASE_URL=postgresql+psycopg://clinic_time_user:change_me@postgres:5432/clinic_time

BACKEND_SECRET_KEY=change_me
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

CLINIC_TIMEZONE=Asia/Seoul
```

## 3.4 Backend Bootstrap

Install:

```bash
cd backend
poetry init
poetry add fastapi uvicorn sqlalchemy psycopg alembic pydantic pydantic-settings python-multipart passlib bcrypt
poetry add --group dev pytest pytest-asyncio httpx ruff mypy
```

Basic backend folders:

```text
backend/app/
├── main.py
├── core/
│   ├── config.py
│   ├── security.py
│   └── permissions.py
├── db/
│   ├── session.py
│   └── base.py
├── models/
├── schemas/
├── services/
├── api/
│   └── routes/
└── utils/
```

## 3.5 Frontend Bootstrap

```bash
npx create-next-app@latest frontend --typescript
cd frontend
npm install zod react-hook-form axios
```

Recommended frontend folders:

```text
frontend/
├── app/
│   ├── login/
│   ├── dashboard/
│   ├── attendance/
│   ├── leave/
│   ├── staff/
│   ├── schedules/
│   ├── reports/
│   └── settings/
├── components/
├── lib/
├── hooks/
└── types/
```

------

# 4. Phase 1 — Authentication and Staff Management

## 4.1 Backend Models

Create the first core tables:

```text
clinics
users
```

### clinics

```text
id
name
timezone
address
ip_whitelist
created_at
updated_at
```

### users

```text
id
clinic_id
name
email
phone
password_hash
role
employment_type
hire_date
termination_date
status
created_at
updated_at
```

Recommended role enum:

```text
OWNER
ADMIN
MANAGER
STAFF
```

Recommended employment type enum:

```text
FULL_TIME
PART_TIME
CONTRACT
TEMPORARY
```

Recommended user status enum:

```text
ACTIVE
INACTIVE
TERMINATED
```

## 4.2 Authentication Endpoints

Implement:

```http
POST /auth/login
POST /auth/logout
GET  /auth/me
POST /auth/change-password
```

## 4.3 Staff Management Endpoints

Implement:

```http
GET    /staff
POST   /staff
GET    /staff/{user_id}
PATCH  /staff/{user_id}
DELETE /staff/{user_id}
```

Important: `DELETE /staff/{id}` should not physically delete the user. It should deactivate the user.

## 4.4 Permission Rules

Initial rules:

| Action           | Owner/Admin | Manager  | Staff |
| ---------------- | ----------- | -------- | ----- |
| Create staff     | Yes         | Optional | No    |
| Edit staff       | Yes         | Optional | No    |
| Deactivate staff | Yes         | No       | No    |
| View all staff   | Yes         | Yes      | No    |
| View own profile | Yes         | Yes      | Yes   |

## 4.5 Frontend Pages

Build:

```text
/login
/dashboard
/staff
/staff/new
/staff/[id]
```

## 4.6 Completion Criteria

Phase 1 is complete when:

- User can log in.
- Authenticated user can access dashboard.
- Admin can create staff.
- Admin can deactivate staff.
- Staff cannot access admin pages.

------

# 5. Phase 2 — Shift and Schedule Management

## 5.1 Backend Models

Create:

```text
shifts
staff_schedules
```

### shifts

```text
id
clinic_id
name
start_time
end_time
break_minutes
crosses_midnight
active
created_at
updated_at
```

### staff_schedules

```text
id
clinic_id
user_id
shift_id
work_date
scheduled_start
scheduled_end
scheduled_break_minutes
status
created_at
updated_at
```

Schedule status enum:

```text
SCHEDULED
OFF
HOLIDAY
CANCELLED
```

## 5.2 API Endpoints

```http
GET    /shifts
POST   /shifts
GET    /shifts/{shift_id}
PATCH  /shifts/{shift_id}
DELETE /shifts/{shift_id}

GET    /schedules
POST   /schedules
PATCH  /schedules/{schedule_id}
DELETE /schedules/{schedule_id}
```

Support query filters:

```http
GET /schedules?start_date=2026-06-01&end_date=2026-06-30
GET /schedules?user_id=...
```

## 5.3 Business Logic

Implement schedule generation:

```text
Input:
- user_id
- shift_id
- date range
- selected weekdays

Output:
- staff_schedules rows
```

Example:

```text
Create weekday 09:00–18:00 schedule for nurse A from June 1 to June 30.
```

## 5.4 Frontend Pages

Build:

```text
/schedules
/schedules/calendar
/shifts
```

Minimum UI:

- Shift template form
- Staff schedule calendar
- Date range assignment
- Staff filter

## 5.5 Completion Criteria

Phase 2 is complete when:

- Admin can create shift templates.
- Admin/manager can assign shifts to staff.
- Staff can view own schedule.
- Schedule data can be queried by date range.

------

# 6. Phase 3 — Clock-In and Clock-Out

## 6.1 Backend Models

Create:

```text
attendance_punches
```

### attendance_punches

```text
id
clinic_id
user_id
punch_type
timestamp
source
ip_address
device_info
geo_lat
geo_lng
qr_code_id
created_at
```

Punch type enum:

```text
CLOCK_IN
CLOCK_OUT
BREAK_START
BREAK_END
MANUAL
```

Source enum:

```text
WEB
MOBILE_WEB
ADMIN
QR
GPS
BIOMETRIC
```

For MVP, implement only:

```text
WEB
MOBILE_WEB
ADMIN
```

## 6.2 API Endpoints

```http
POST /attendance/clock-in
POST /attendance/clock-out
GET  /attendance/today
GET  /attendance/me
```

Admin/manager endpoints:

```http
GET /attendance/daily
GET /attendance/monthly
```

## 6.3 Clock-In Logic

Pseudo-logic:

```python
def clock_in(user_id, timestamp):
    today = get_work_date(timestamp)

    if has_active_session(user_id):
        raise Error("Already clocked in")

    create_punch(
        user_id=user_id,
        punch_type="CLOCK_IN",
        timestamp=timestamp,
        source="WEB",
    )

    recalculate_attendance_day(user_id, today)
```

## 6.4 Clock-Out Logic

```python
def clock_out(user_id, timestamp):
    if not has_active_session(user_id):
        raise Error("No active clock-in found")

    create_punch(
        user_id=user_id,
        punch_type="CLOCK_OUT",
        timestamp=timestamp,
        source="WEB",
    )

    recalculate_attendance_day(user_id, get_work_date(timestamp))
```

## 6.5 Frontend Pages

Build:

```text
/attendance/today
```

Staff home page should show:

```text
Today’s date
Assigned shift
Current status
Clock In / Clock Out button
Last punch time
Warning if missing punch
```

## 6.6 Completion Criteria

Phase 3 is complete when:

- Staff can clock in.
- Staff can clock out.
- Duplicate clock-in is prevented.
- Clock-out without clock-in is prevented.
- Raw punch records are stored.

------

# 7. Phase 4 — Attendance Calculation Engine

This is one of the most important parts of the system.

## 7.1 Backend Models

Create:

```text
attendance_days
```

### attendance_days

```text
id
clinic_id
user_id
work_date
schedule_id
scheduled_start
scheduled_end
scheduled_break_minutes
actual_start
actual_end
actual_break_minutes
regular_minutes
overtime_minutes
night_minutes
holiday_minutes
late_minutes
early_leave_minutes
status
is_locked
calculated_at
created_at
updated_at
```

Attendance status enum:

```text
NOT_STARTED
WORKING
COMPLETED
LATE
EARLY_LEAVE
ABSENT
LEAVE
MISSING_PUNCH
MANUALLY_CORRECTED
LOCKED
```

## 7.2 Calculation Service

Create:

```text
services/attendance_calculator.py
```

Core function:

```python
def recalculate_attendance_day(user_id: UUID, work_date: date) -> AttendanceDay:
    schedule = get_schedule(user_id, work_date)
    punches = get_punches(user_id, work_date)
    approved_leave = get_approved_leave(user_id, work_date)
    corrections = get_approved_corrections(user_id, work_date)

    summary = calculate_day(
        schedule=schedule,
        punches=punches,
        approved_leave=approved_leave,
        corrections=corrections,
    )

    save_attendance_day(summary)
    return summary
```

## 7.3 Calculation Rules

### Normal completed day

```text
actual_start = first CLOCK_IN
actual_end = last CLOCK_OUT
worked_minutes = actual_end - actual_start - break_minutes
```

### Late

```text
late_minutes = max(0, actual_start - scheduled_start)
```

### Early leave

```text
early_leave_minutes = max(0, scheduled_end - actual_end)
```

### Overtime

```text
overtime_minutes = max(0, worked_minutes - scheduled_minutes)
```

### Missing punch

```text
If clock-in exists but clock-out does not:
    status = MISSING_PUNCH
```

### Absent

```text
If scheduled but no punch and no approved leave:
    status = ABSENT
```

### Approved leave

```text
If full-day approved leave exists:
    status = LEAVE
```

## 7.4 Edge Cases to Implement Early

Handle:

- No schedule but staff clocks in
- Schedule crossing midnight
- Clock-in before scheduled start
- Clock-out after midnight
- Missing clock-out
- Approved half-day leave
- Locked attendance day

## 7.5 Unit Tests

Create tests for:

```text
Normal workday
Late arrival
Early leave
Overtime
Missing clock-out
Absent day
Full-day leave
Half-day leave
Night shift
Schedule crossing midnight
```

## 7.6 Completion Criteria

Phase 4 is complete when:

- Daily attendance summary is created from punches.
- Attendance is recalculated after each punch.
- Core edge cases are tested.
- Manager dashboard can show daily status.

------

# 8. Phase 5 — Attendance Correction Workflow

## 8.1 Backend Models

Create:

```text
attendance_correction_requests
```

### attendance_correction_requests

```text
id
clinic_id
user_id
work_date
requested_start
requested_end
reason
status
approved_by
approved_at
rejected_reason
created_at
updated_at
```

Status enum:

```text
PENDING
APPROVED
REJECTED
CANCELLED
```

## 8.2 API Endpoints

Staff:

```http
POST /attendance/correction-requests
GET  /attendance/correction-requests/me
```

Manager/admin:

```http
GET  /attendance/correction-requests
POST /attendance/correction-requests/{id}/approve
POST /attendance/correction-requests/{id}/reject
```

## 8.3 Approval Logic

When approved:

```text
1. Mark correction request as APPROVED.
2. Store approver and approval timestamp.
3. Recalculate attendance day using correction values.
4. Create audit log.
```

Important: Do not modify raw punch records.

## 8.4 Frontend Pages

Build:

```text
/attendance/corrections/new
/attendance/corrections
/approvals/corrections
```

## 8.5 Completion Criteria

Phase 5 is complete when:

- Staff can request correction.
- Manager can approve/reject.
- Approved correction updates attendance summary.
- Raw punches remain unchanged.
- Audit log is created.

------

# 9. Phase 6 — Leave Management

## 9.1 Backend Models

Create:

```text
leave_types
leave_requests
```

### leave_types

```text
id
clinic_id
name
paid
deducts_annual_leave
unit
requires_approval
active
created_at
updated_at
```

Leave unit enum:

```text
DAY
HALF_DAY
HOUR
```

### leave_requests

```text
id
clinic_id
user_id
leave_type_id
start_datetime
end_datetime
duration_days
duration_hours
reason
status
approved_by
approved_at
rejected_reason
created_at
updated_at
```

Leave request status enum:

```text
PENDING
APPROVED
REJECTED
CANCELLED
```

## 9.2 API Endpoints

Leave types:

```http
GET    /leave/types
POST   /leave/types
PATCH  /leave/types/{id}
DELETE /leave/types/{id}
```

Leave requests:

```http
POST /leave/requests
GET  /leave/requests/me
GET  /leave/requests
POST /leave/requests/{id}/approve
POST /leave/requests/{id}/reject
POST /leave/requests/{id}/cancel
```

## 9.3 Leave Request Validation

Validate:

```text
User exists and is active
Leave type exists and is active
Start date is before end date
Requested dates are not locked
No duplicate overlapping leave request
Annual leave balance is sufficient (tenure_based types only)
Non-annual per-request maximum exceeded: allow submission, return policy_warning
```

## 9.4 Approval Logic

When approved:

```text
1. Check leave balance.
2. Check minimum staffing rule.
3. Mark request as APPROVED.
4. Deduct balance if leave type requires deduction.
5. Recalculate affected attendance days.
6. Create audit log.
```

## 9.5 Frontend Pages

Build:

```text
/leave/request
/leave/my
/leave/balances
/approvals/leave
/leave/calendar
```

## 9.6 Completion Criteria

Phase 6 is complete when:

- Staff can request leave.
- Manager can approve/reject leave.
- Approved leave appears in attendance.
- Rejected leave does not affect attendance or balance.
- Pending leave is visible to manager.

------

# 10. Phase 7 — Leave Balance Engine

## 10.1 Backend Models

Create:

```text
leave_balances
leave_balance_adjustments
leave_policies
```

### leave_balances

```text
id
clinic_id
user_id
year
accrued_days
used_days
pending_days
adjusted_days
remaining_days
updated_at
```

### leave_balance_adjustments

```text
id
clinic_id
user_id
year
adjustment_days
reason
created_by
created_at
```

### leave_policies

```text
id
clinic_id
name
applies_from
annual_base_days
first_year_monthly_accrual
max_annual_days
carryover_allowed
active
created_at
updated_at
```

## 10.2 Implemented Accrual Engine

Annual leave is calculated automatically from hire date using a dual-track engine in `backend/app/core/leave_accrual.py`, exposed to balances via `backend/app/core/kr_labor.py`.

### Legal minimum track (hire-date basis)

```text
< 1 year:     1 day per completed month after hire (max 11)
1-year date:  15 days (assumes 80%+ attendance)
3+ years:     15 + floor((completed_years - 1) / 2), max 25
```

### Fiscal policy track (calendar-year bulk grant)

Default fiscal year: January 1 (`LEAVE_FISCAL_START_MONTH` / `LEAVE_FISCAL_START_DAY`).

```text
Hire year:              monthly accrual (1 day/month, max 11)
First fiscal Jan 1:     proportional grant for prior partial year
Subsequent fiscal Jan 1: regular annual grant by completed service years
```

### Legal adjustment

When fiscal grants fall below the legal minimum, `legal_adjustment` events top up the difference. Mode is configurable:

```text
anniversary_top_up  — adjust on each legal grant date and as_of (default)
termination_only    — settle only on termination_date
none                — no automatic top-up
```

### Calendar-year balance display

`annual_leave_for_calendar_year()` returns entitlement granted during a calendar year. **Before the 1-year hire anniversary**, only monthly accrual events in that year are counted. After the anniversary, the full dual-track total (including fiscal grants and adjustments) applies.

### Leave type semantics

```text
tenure_based = true   → annual leave; yearly balance allocation from hire date
tenure_based = false  → usage-only tracking; default_days_per_year = max per single request
```

Only annual leave supports balance adjustments. Non-annual requests exceeding the per-request max are allowed but return `policy_warning` on the API response.

## 10.3 Configuration

Environment variables (mirrored in `.env.example` and `dev.env.example`):

```text
LEAVE_FISCAL_START_MONTH=1
LEAVE_FISCAL_START_DAY=1
LEAVE_FISCAL_ROUNDING=round_2
LEAVE_ADJUSTMENT_MODE=anniversary_top_up
```

## 10.4 Balance Calculation

```text
remaining_days = accrued_days + adjusted_days - used_days - pending_days
```

You may display both:

```text
Remaining excluding pending
Remaining including pending
```

## 10.5 API Endpoints

```http
GET  /leave/balances/me
GET  /leave/balances
PATCH /leave/balances/{id}
POST /leave/balances/{id}/adjust
```

## 10.6 Completion Criteria

Phase 7 is complete when:

- Staff can view own balance.
- Manager can view balance during approval.
- Approved annual leave deducts balance.
- Manual balance adjustment requires reason.
- Balance changes are audited.

------

# 11. Phase 8 — Reports and Exports

## 11.1 Backend Report Services

Create:

```text
services/report_service.py
services/export_service.py
```

## 11.2 Reports to Implement

MVP reports:

```text
Daily attendance report
Monthly attendance summary
Leave usage report
Payroll export
Missing-punch report
Late/early-leave report
```

## 11.3 API Endpoints

```http
GET /reports/daily-attendance?date=2026-06-01
GET /reports/monthly-attendance?month=2026-06
GET /reports/leave-usage?year=2026
GET /reports/payroll-export?month=2026-06&format=xlsx
```

## 11.4 Excel Export Columns

```text
Staff Name
Employment Type
Month
Scheduled Days
Worked Days
Regular Hours
Overtime Hours
Night Hours
Holiday Hours
Late Count
Late Minutes
Early Leave Count
Early Leave Minutes
Annual Leave Used
Unpaid Leave Used
Missing Punch Count
Correction Count
Notes
```

## 11.5 Implementation Detail

Use Python package:

```bash
poetry add openpyxl
```

Generate `.xlsx` server-side.

## 11.6 Completion Criteria

Phase 8 is complete when:

- Admin can view monthly summary.
- Admin can export Excel.
- Exported values match database summary.
- Reports can be filtered by month and staff.

------

# 12. Phase 9 — Monthly Closing and Audit Log

## 12.1 Backend Models

Create:

```text
monthly_closings
audit_logs
```

### monthly_closings

```text
id
clinic_id
month
status
locked_by
locked_at
unlocked_by
unlocked_at
unlock_reason
created_at
updated_at
```

Status enum:

```text
OPEN
LOCKED
UNLOCKED
```

### audit_logs

```text
id
clinic_id
actor_id
entity_type
entity_id
action
before_json
after_json
reason
created_at
```

## 12.2 Monthly Closing API

```http
GET  /months/{month}/status
POST /months/{month}/lock
POST /months/{month}/unlock
```

## 12.3 Locking Rules

Before locking, system should check:

```text
Pending leave requests
Pending correction requests
Missing punches
Unresolved attendance days
```

Admin can still lock with override, but reason is required.

## 12.4 Audit Events

Audit these events:

```text
User created
User deactivated
Role changed
Schedule changed
Clock correction approved
Clock correction rejected
Leave approved
Leave rejected
Leave balance adjusted
Month locked
Month unlocked
Report exported
```

## 12.5 Completion Criteria

Phase 9 is complete when:

- Admin can lock a month.
- Locked records cannot be changed by staff or manager.
- Admin can unlock with reason.
- Key actions are visible in audit log.

------

# 13. Phase 10 — Testing, Deployment, and Hardening

## 13.1 Backend Testing

Test layers:

```text
Unit tests
Service tests
API tests
Permission tests
Calculation tests
```

Critical test cases:

```text
Staff cannot view another staff member’s records.
Manager can approve leave.
Staff cannot approve own leave.
Raw punches are not modified by correction.
Locked month blocks edits.
Leave approval deducts balance.
Rejected leave does not deduct balance.
```

## 13.2 Frontend Testing

Minimum:

```text
Login flow
Clock-in/out flow
Leave request form
Manager approval flow
Report export button
Permission-based navigation
```

Use:

```text
Playwright for end-to-end tests
React Testing Library for components, optional
```

## 13.3 Security Checklist

Before production:

```text
Use HTTPS
Hash passwords
Use HTTP-only secure cookies if session-based
Validate all inputs server-side
Enforce role checks server-side
Protect admin endpoints
Rate-limit login attempts
Log sensitive admin actions
Disable debug mode
Set CORS correctly
Backup database daily
```

## 13.4 Deployment Checklist

Docker Compose production services:

```text
postgres
backend
frontend
nginx
backup
```

Production environment:

```text
Strong database password
Strong secret key
HTTPS certificate
Firewall configured
Database volume mounted
Backup directory mounted
Log rotation configured
```

## 13.5 Backup Strategy

Minimum:

```text
Daily PostgreSQL dump
Keep 14 daily backups
Keep 3 monthly backups
Test restore once before launch
```

Example backup command:

```bash
pg_dump -U clinic_time_user -d clinic_time > backup_$(date +%Y%m%d).sql
```

## 13.6 Completion Criteria

Phase 10 is complete when:

- Application runs in Docker Compose.
- Backup and restore have been tested.
- Core flows pass manual QA.
- Admin account is secured.
- Clinic owner can export monthly report.
- Staff can use mobile clock-in/out reliably.

------

# 14. Recommended Database Migration Order

Create migrations in this order:

```text
001_create_clinics
002_create_users
003_create_shifts
004_create_staff_schedules
005_create_attendance_punches
006_create_attendance_days
007_create_attendance_correction_requests
008_create_leave_types
009_create_leave_requests
010_create_leave_balances
011_create_leave_balance_adjustments
012_create_leave_policies
013_create_monthly_closings
014_create_audit_logs
```

------

# 15. Recommended API Implementation Order

Build endpoints in this order:

```text
1. /auth
2. /staff
3. /shifts
4. /schedules
5. /attendance/clock-in
6. /attendance/clock-out
7. /attendance/today
8. /attendance/monthly
9. /attendance/correction-requests
10. /leave/types
11. /leave/requests
12. /leave/balances
13. /reports/monthly-attendance
14. /reports/payroll-export
15. /months/{month}/lock
16. /audit-logs
```

------

# 16. Recommended Frontend Implementation Order

Build pages in this order:

```text
1. Login
2. Staff dashboard
3. Clock-in/out page
4. Admin staff management
5. Shift settings
6. Schedule calendar
7. My attendance
8. Correction request
9. Manager correction approval
10. Leave request
11. Manager leave approval
12. Leave balance
13. Monthly report
14. Payroll export
15. Audit log
16. Settings
```

------

# 17. Detailed MVP Screen List

## Staff Screens

```text
/login
/dashboard
/attendance/today
/attendance/my
/attendance/corrections/new
/leave/request
/leave/my
/leave/balance
```

## Manager Screens

```text
/manager/dashboard
/manager/attendance/daily
/manager/approvals/leave
/manager/approvals/corrections
/manager/schedules
```

## Admin Screens

```text
/admin/staff
/admin/shifts
/admin/schedules
/admin/leave-types
/admin/leave-balances
/admin/reports/monthly
/admin/reports/payroll
/admin/audit-logs
/admin/settings
```

------

# 18. Business Logic Implementation Priorities

## Highest Priority

Implement correctly first:

```text
Raw punch immutability
Attendance recalculation
Leave approval and balance deduction
Permission checks
Audit logging
Monthly locking
```

## Medium Priority

Implement after core flows:

```text
Minimum staffing warning
Holiday work calculation
Night work calculation
Overtime report
Advanced schedule templates
```

## Low Priority for MVP

Delay:

```text
GPS clock-in
QR clock-in
Biometric integration
Payroll vendor integration
Mobile native app
Multi-branch support
```

------

# 19. Suggested Service Layer Design

Backend services:

```text
AuthService
UserService
ShiftService
ScheduleService
AttendancePunchService
AttendanceCalculationService
CorrectionRequestService
LeaveRequestService
LeaveBalanceService
ReportService
ExportService
MonthlyClosingService
AuditLogService
```

Do not put business logic directly inside route handlers.

Recommended route handler style:

```python
@router.post("/attendance/clock-in")
def clock_in(
    current_user: User = Depends(get_current_user),
    service: AttendancePunchService = Depends(),
):
    return service.clock_in(current_user.id)
```

Business rules should live in the service layer.

------

# 20. Attendance Calculation Design

Use a deterministic calculation pipeline:

```text
Input:
1. Schedule
2. Raw punches
3. Approved leave
4. Approved corrections
5. Holiday data
6. Clinic policy

Process:
1. Determine expected working period.
2. Determine actual working period.
3. Apply approved corrections.
4. Apply approved leave.
5. Calculate regular, overtime, night, holiday minutes.
6. Determine attendance status.
7. Save attendance_day summary.

Output:
attendance_days row
```

The same input should always produce the same output.

------

# 21. Leave Management Design

Use an approval state machine:

```text
PENDING → APPROVED
PENDING → REJECTED
PENDING → CANCELLED
APPROVED → CANCELLATION_REQUESTED
CANCELLATION_REQUESTED → CANCELLED
```

For MVP, you may simplify to:

```text
PENDING
APPROVED
REJECTED
CANCELLED
```

But if approved leave cancellation matters operationally, add `CANCELLATION_REQUESTED`.

------

# 22. Permission Matrix for MVP

| Feature              | Owner/Admin | Manager | Staff |
| -------------------- | ----------- | ------- | ----- |
| Clock in/out self    | Yes         | Yes     | Yes   |
| View own attendance  | Yes         | Yes     | Yes   |
| View all attendance  | Yes         | Yes     | No    |
| Create staff         | Yes         | No      | No    |
| Edit staff           | Yes         | No      | No    |
| Create shifts        | Yes         | Yes     | No    |
| Assign schedules     | Yes         | Yes     | No    |
| Request leave        | Yes         | Yes     | Yes   |
| Approve leave        | Yes         | Yes     | No    |
| Adjust leave balance | Yes         | No      | No    |
| Request correction   | Yes         | Yes     | Yes   |
| Approve correction   | Yes         | Yes     | No    |
| Export report        | Yes         | Yes     | No    |
| Lock month           | Yes         | No      | No    |
| View audit log       | Yes         | No      | No    |
| Configure settings   | Yes         | No      | No    |

Important rule: a manager should not approve their own leave or correction request unless explicitly allowed by admin policy.

------

# 23. Example Backend Implementation Milestone

## Milestone 1

```text
Auth + staff CRUD
```

Deliverable:

- Admin can create staff.
- Staff can log in.

## Milestone 2

```text
Schedule + shift
```

Deliverable:

- Manager can assign schedules.
- Staff can see today’s shift.

## Milestone 3

```text
Clock-in/out
```

Deliverable:

- Staff can clock in/out.
- Daily attendance summary is generated.

## Milestone 4

```text
Leave request
```

Deliverable:

- Staff can request leave.
- Manager can approve leave.
- Leave appears in attendance.

## Milestone 5

```text
Corrections
```

Deliverable:

- Staff can request missed-punch correction.
- Manager can approve correction.
- Attendance is recalculated.

## Milestone 6

```text
Reports
```

Deliverable:

- Admin can export monthly Excel report.

## Milestone 7

```text
Audit + monthly lock
```

Deliverable:

- System is suitable for real clinic pilot.

------

# 24. Suggested Git Branch Strategy

For a small project:

```text
main
develop
feature/auth
feature/staff
feature/schedules
feature/attendance
feature/leave
feature/reports
feature/audit
```

Merge to `main` only after:

```text
Tests pass
Manual QA completed
Migration verified
No critical security issue
```

------

# 25. Manual QA Checklist Before Pilot

## Staff QA

```text
Can log in
Can clock in
Can clock out
Can view today’s status
Can request leave
Can request correction
Cannot see other staff data
```

## Manager QA

```text
Can view daily attendance
Can see late/absent staff
Can approve leave
Can reject leave
Can approve correction
Can assign schedules
Cannot access admin-only settings
```

## Admin QA

```text
Can create staff
Can deactivate staff
Can create shifts
Can adjust leave balance
Can export report
Can lock month
Can view audit logs
Can restore database backup
```

------

# 26. Launch Plan

## Pilot Setup

Before real use:

```text
Create clinic profile
Create admin account
Create staff accounts
Create shift templates
Input initial leave balances
Create current month schedule
Test clock-in/out
Test leave request
Test Excel export
Train staff for 10 minutes
```

## Pilot Duration

Recommended pilot:

```text
2 to 4 weeks
```

During pilot, keep parallel records in Excel or paper until confidence is established.

## Go-Live Criteria

Go live when:

```text
Clock-in/out success rate is above 90%
Monthly report matches manual records
Managers can approve leave without support
No critical permission bugs are found
Backup restore is verified
```

------

# 27. Post-MVP Enhancements

After the MVP is stable, add:

```text
QR-code clock-in
Clinic IP restriction
GPS verification
KakaoTalk or SMS reminders
Automatic public holiday import
Advanced annual leave accrual
Overtime approval
Part-time leave policy
Multi-branch support
Payroll integration
Native mobile app
```

Recommended first post-MVP enhancement:

```text
Clinic IP restriction + QR-code clock-in
```

This gives a good balance of usability and anti-fraud control without biometric complexity.

------

# 28. Final Development Principle

The most important architectural rule is:

```text
Raw attendance punches must be immutable.
Corrections must be approval-based.
Calculated attendance summaries must be reproducible.
```

This design protects the clinic from payroll disputes, accidental edits, and unclear historical records.