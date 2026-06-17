# Detailed Implementation Plan

# ClinicTime MVP Implementation Plan

This plan describes how to build the ClinicTime MVP from the current documentation-only repository into a working Next.js, FastAPI, and PostgreSQL application. It follows the phase order in `docs/2_DevelopmentGuide.md` and maps to backlog items in `docs/3_Backlog.md`.

## 1. Delivery Strategy

Build the MVP in vertical slices, but keep the backend domain model ahead of the UI by one phase. Each phase should end with working API endpoints, database migrations, focused tests, and at least one usable frontend path where relevant.

Primary quality gates:

- Backend tests pass with `pytest`.
- Backend lint and type checks pass with `ruff check .` and `mypy app`.
- Frontend build and tests pass with `npm run build` and `npm test` once configured.
- Docker Compose can start all required services.
- Role-based access is verified for every protected workflow.

## 2. Technical Baseline

### Repository Layout

Create the target monorepo structure:

```text
backend/
  app/
  alembic/
  tests/
frontend/
  app/
  components/
  hooks/
  lib/
  types/
infra/
  nginx/
  backup/
docker-compose.yml
.env.example
README.md
```

### Core Technology Choices

- Backend: FastAPI, Python 3.12+, SQLAlchemy 2.x, Alembic, Pydantic, PostgreSQL.
- Frontend: Next.js, React, TypeScript, React Hook Form, Zod, Tailwind CSS or MUI.
- Authentication: email/password with secure HTTP-only cookie sessions or JWT access/refresh tokens.
- Deployment: Docker Compose for frontend, backend, and PostgreSQL.

## 3. Phase 0: Foundation

Backlog: `CT-001` through `CT-005`.

Implementation steps:

1. Create repository folders and baseline README.
2. Add `.env.example` with database, auth, frontend/backend URL, and `CLINIC_TIMEZONE`.
3. Configure `docker-compose.yml` with `postgres`, `backend`, and `frontend`.
4. Bootstrap FastAPI with `/health`, settings loader, database session, and test setup.
5. Bootstrap Next.js with shared layout, API client placeholder, and route folders.
6. Add formatting, linting, typing, and CI scripts.

Exit criteria:

- `docker compose up --build` starts all services.
- Backend `/health` returns success.
- Empty test suites and lint commands run successfully.

## 4. Phase 1: Authentication and Staff Management

Backlog: `CT-101` through `CT-105`.

Database work:

- Create `clinics` and `users`.
- Add enums for role, employment type, and user status.
- Add unique email constraints scoped appropriately for the MVP.

Backend work:

- Implement password hashing with Argon2id or bcrypt.
- Implement `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`, and `POST /auth/change-password`.
- Implement staff endpoints: `GET /staff`, `POST /staff`, `GET /staff/{id}`, `PATCH /staff/{id}`, and soft-delete/deactivate.
- Add permission dependencies for owner/admin, manager, and staff.

Frontend work:

- Build `/login`, `/dashboard`, `/staff`, `/staff/new`, and `/staff/[id]`.
- Add protected route handling and role-aware navigation.

Tests:

- Login success/failure.
- Deactivated user cannot log in.
- Staff cannot access admin-only staff management.
- Staff deactivation preserves historical user row.

Exit criteria:

- Admin can create and deactivate staff.
- Staff can log in and view only allowed data.

## 5. Phase 2: Shift and Schedule Management

Backlog: `CT-201` through `CT-203`.

Database work:

- Create `shifts` and `staff_schedules`.
- Store scheduled start/end datetimes, break minutes, status, and overnight shift support.

Backend work:

- Implement shift CRUD endpoints.
- Implement schedule CRUD endpoints with `start_date`, `end_date`, and `user_id` filters.
- Add schedule generation by date range and selected weekdays.

Frontend work:

- Build `/shifts`, `/schedules`, and `/schedules/calendar`.
- Support shift template creation, staff assignment, and staff/date filtering.

Tests:

- Schedule generation skips unselected weekdays.
- Overnight shifts calculate scheduled end on the following date.
- Staff can read own schedule but cannot edit schedules.

Exit criteria:

- Managers can assign schedules.
- Staff can view their schedule by date.

## 6. Phase 3: Clock-In and Clock-Out

Backlog: `CT-301` through `CT-303`.

Database work:

- Create immutable `attendance_punches`.
- Store punch type, timestamp, source, IP address, device info, and creation timestamp.

Backend work:

- Implement `POST /attendance/clock-in`, `POST /attendance/clock-out`, `GET /attendance/today`, and `GET /attendance/me`.
- Prevent duplicate active clock-in.
- Prevent clock-out without an active session.
- Capture source as `WEB`, `MOBILE_WEB`, or `ADMIN` for MVP.

Frontend work:

- Build `/attendance/today`.
- Show today’s date, assigned shift, current status, last punch, and clock button.

Tests:

- Duplicate clock-in is rejected.
- Clock-out without clock-in is rejected.
- Raw punches are never updated by normal attendance flows.

Exit criteria:

- A staff member can complete a basic work session from the UI.

## 7. Phase 4: Attendance Calculation Engine

Backlog: `CT-401` through `CT-403`.

Database work:

- Create `attendance_days`.
- Store schedule snapshot, actual start/end, break minutes, regular minutes, overtime minutes, late minutes, early-leave minutes, night minutes, holiday minutes, and status.

Backend work:

- Implement a recalculation service that derives daily summaries from schedules, raw punches, approved corrections, and leave.
- Keep raw punches separate from calculated summaries.
- Trigger recalculation after clock-in, clock-out, correction approval, schedule change, and leave approval.

Frontend work:

- Add exception data to manager dashboard.
- Show attendance status in staff views.

Tests:

- Late arrival calculates late minutes.
- Early clock-out calculates early-leave minutes.
- Missing clock-out marks missing punch.
- Recalculation is deterministic from source records.

Exit criteria:

- Daily attendance summaries match schedules and punches for normal, late, early, absent, and missing-punch cases.

## 8. Phase 5: Attendance Corrections

Backlog: `CT-501` through `CT-503`.

Database work:

- Create `attendance_correction_requests`.
- Store requested times, reason, status, reviewer, review note, and timestamps.

Backend work:

- Implement staff submission endpoint.
- Implement manager/admin approve and reject endpoints.
- On approval, create correction record and recalculate affected attendance day.
- Audit approvals and rejections.

Frontend work:

- Build correction request form.
- Build manager review list with original punch data and requested changes.

Tests:

- Staff cannot directly edit attendance.
- Approved correction updates summary but not raw punches.
- Rejection leaves summary unchanged.

Exit criteria:

- Missed-punch corrections are request-based, reviewable, and auditable.

## 9. Phase 6: Leave Management

Backlog: `CT-601` through `CT-606`.

Database work:

- Create `leave_types` and `leave_requests`.
- Create `leave_import_batches` for CSV upload metadata, validation results, import status, and actor.
- Store unit, paid/unpaid flag, balance deduction flag, approval requirement, status, reason, reviewer, and review note.
- Add fields to distinguish leave source, such as `REQUESTED`, `ADMIN_HISTORICAL`, and `CSV_IMPORT`.
- Store import batch ID or admin entry reference for historical records.

Backend work:

- Implement leave type management.
- Implement leave request submission, cancellation while pending, approval, and rejection.
- Add minimum staffing warning calculation before approval.
- Implement admin-only manual historical leave entry for existing employees.
- Implement CSV historical leave import with dry-run validation and commit steps.
- Validate CSV rows for employee identity, leave type, date/time range, unit, duration, and duplicate records.
- Treat historical imported leave as already approved while preserving source and audit metadata.

Initial CSV columns:

```text
employee_email,leave_type,start_date,end_date,start_time,end_time,unit,duration,reason,source_note
```

`start_time` and `end_time` are required only for hourly leave. Imports should reject unknown employees, inactive leave types, negative durations, invalid date ranges, and rows that duplicate an existing historical leave record.

Frontend work:

- Build staff leave request flow.
- Build manager pending leave review.
- Add team leave calendar.
- Build admin historical leave entry form.
- Build CSV import screen with template download, upload, validation preview, row errors, and commit action.

Tests:

- Pending leave appears for manager review.
- Rejected leave does not deduct balance.
- Approved leave appears in schedule and attendance views.
- Staffing warning is shown before approval when configured rules are violated.
- Manual historical leave updates leave history and balance.
- CSV dry run reports invalid rows without writing records.
- CSV commit imports valid rows and creates audit entries.

Exit criteria:

- Staff can request leave, managers can approve or reject it, and admins can load existing employees' historical leave manually or by CSV.

## 10. Phase 7: Leave Balance Engine

Backlog: `CT-701` through `CT-704`.

Database work:

- Create `leave_balances` and `leave_balance_adjustments`.
- Track accrued, used, pending, adjusted, and remaining days by year.
- Store opening balance entries separately from normal accrual and usage calculations.

Backend work:

- Calculate balance changes from approved leave.
- Show pending leave separately from used leave.
- Add admin adjustment workflow with required reason.
- Add opening balance workflow for onboarding existing employees.
- Recalculate balances after historical leave import and keep import results auditable.

Frontend work:

- Show staff remaining annual leave.
- Show balance during manager approval.
- Build admin adjustment UI.
- Build admin opening balance entry or upload flow for existing employees.

Tests:

- Approved annual leave deducts balance.
- Rejected leave does not deduct balance.
- Manual adjustment requires reason and creates audit log entry.
- Opening balance affects remaining leave.
- Imported historical leave deducts from the correct year and balance bucket.

Exit criteria:

- Annual leave balance can be initialized, imported, viewed, adjusted, and audited.

## 11. Phase 8: Reports and Exports

Backlog: `CT-801` through `CT-803`.

Backend work:

- Implement daily attendance, monthly summary, leave usage, late/early-leave, overtime, missing-punch, and payroll export queries.
- Generate CSV and Excel exports server-side.
- Ensure export values use the same query path as on-screen reports.

Frontend work:

- Build monthly report screen with month, staff, role, and employment filters.
- Add exception list, export buttons, and report summary table.

Tests:

- Export totals match API report totals.
- Filters apply consistently.
- Report generation completes within target size constraints.

Exit criteria:

- Admin can export payroll-ready monthly attendance data.

## 12. Phase 9: Monthly Closing and Audit Log

Backlog: `CT-901` through `CT-903`.

Database work:

- Create `audit_logs` and `monthly_closings`.
- Add lock checks to mutable attendance, schedule, correction, and leave workflows.

Backend work:

- Centralize audit logging for sensitive actions.
- Implement month lock and unlock with required reason.
- Show unresolved issues before locking.

Frontend work:

- Add audit log viewer for admin.
- Add monthly lock/unlock actions to reports screen.

Tests:

- Locked records cannot be edited by staff or managers.
- Admin unlock requires reason.
- Lock, unlock, approvals, role changes, and balance adjustments create audit entries.

Exit criteria:

- Payroll period records can be locked and later unlocked only through an auditable admin workflow.

## 13. Phase 10: Hardening and Release Preparation

Backlog: `CT-1001` through `CT-1004`.

Implementation steps:

1. Expand end-to-end coverage for auth, staff, schedules, punches, corrections, leave, reports, and locking.
2. Add timezone tests for `CLINIC_TIMEZONE`, overnight shifts, month boundaries, and daylight-saving-safe date logic where applicable.
3. Review authorization coverage for every endpoint.
4. Add daily database backup script and restore notes.
5. Add production deployment notes for HTTPS, secrets, database persistence, and reverse proxy configuration.
6. Perform seed-data testing with 3 to 30 employees and at least one month of records.

Exit criteria:

- MVP workflows pass with seeded clinic data.
- Deployment and backup instructions are documented.
- Security-sensitive workflows are covered by tests.

## 14. Cross-Cutting Implementation Rules

- Never physically delete users, raw punches, audit logs, or payroll-relevant history through normal application flows.
- Store raw events separately from calculated summaries.
- Make attendance and leave calculations deterministic and recalculable.
- Require server-side authorization even when frontend routes are hidden.
- Require reason fields for manual corrections, balance adjustments, overrides, unlocks, and rejections where applicable.
- Keep post-MVP features such as GPS, QR code, biometric devices, notifications, and multi-branch support out of the MVP path.

## 15. Suggested Milestones

| Milestone | Scope | Target Outcome |
| --- | --- | --- |
| M1 | Foundation and auth | Admin can log in and manage staff. |
| M2 | Scheduling and punching | Staff can view schedule and clock in/out. |
| M3 | Attendance engine | Manager can see calculated daily attendance and exceptions. |
| M4 | Corrections and leave | Staff requests are approved or rejected through auditable workflows. |
| M5 | Reports and locking | Admin can export monthly data and lock reviewed periods. |
| M6 | Hardening | MVP is tested, documented, and ready for pilot deployment. |

## 16. Initial Definition of Done

Each feature is done when:

- Database migration is committed.
- API schemas and endpoints are implemented.
- Role checks are covered by tests.
- Frontend flow handles loading, success, validation, and error states.
- Relevant audit events are emitted for sensitive actions.
- Documentation or `.env.example` is updated when configuration changes.
